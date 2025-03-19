from dnslib import DNSRecord, DNSHeader, DNSBuffer, DNSQuestion, RR, QTYPE, RCODE
from socket import socket, SOCK_DGRAM, AF_INET
from os import system, name

"""
Elijah Morgan
CIS 457 02
"""

# There are 13 root servers defined at https://www.iana.org/domains/root/servers

ROOT_SERVER = "199.7.83.42"    # ICANN Root Server
DNS_PORT = 53

# Formatting constants
LINELEN = 150
BREAKLINE = f"\n{'=' * LINELEN}\n"
WEAKLINE = f"\n\n{'-' * LINELEN}\n"
LONGSPACE = "\n" * 2

class Cache:
  #TODO If I implement IPv6 for extra credit, make a child class for IPv6
  def __init__(self):
    # Key: domain, Value: IP address
    self.cache = {}
    self.length = 0
  
  def _inCache(self, key:str) -> bool:
    return key in self.cache
  
  def add(self, key:str, value:str) -> None:
    # This will overwrite existing values!
    self.cache[key] = value
    self.length += 1

  def remove(self, key) -> None:
    if self._inCache(key):
      del self.cache[key]
      self.length -= 1
    else:
      print(f"Domain \"{key}\" not found in cache")

  def list(self) -> tuple[tuple[str], tuple[str]]:
    return tuple(self.cache.keys()), tuple(self.cache.values())
  
  def clear(self) -> None:
    self.cache.clear()
    self.length = 0

  def get(self, key:str) -> str|None:
    if self._inCache(key):
      return self.cache[key]
    else:
      print(f"Domain \"{key}\" not found in cache")
      return None

def domainValidation(domain:str) -> bool:
  # "validation" in words only, mostly to stop mispelled commands from crashing the program.
  if domain.startswith(".") and domain != ".":
    return False
  return True

def clearScreen() -> None:
  system('cls' if name == 'nt' else 'clear')

def get_dns_record(udp_socket, domain:str, parent_server: str, record_type) -> list[RR]:
  q = DNSRecord.question(domain, qtype = record_type)
  q.header.rd = 0   # Recursion Desired?  NO
  print(LONGSPACE, "DNS query", repr(q))
  udp_socket.sendto(q.pack(), (parent_server, DNS_PORT))
  pkt, _ = udp_socket.recvfrom(8192)
  buff = DNSBuffer(pkt)
  
  # A/AAAA queries typically return information in the answer section.
  # NS queries typically return information in the authority section.
  answers = []
  authorities = []
  additional = []

  """
  RFC1035 Section 4.1 Format
  
  The top level format of DNS message is divided into five sections:
  1. Header
  2. Question
  3. Answer
  4. Authority
  5. Additional
  
  NS queries typically return information in the authority section.
  A/AAAA queries typically return information in the answer section.
  """
  
  # ==================== 1. Parse header =============================
  header = DNSHeader.parse(buff)
  
  #print("DNS header", repr(header), WEAKLINE)
  if q.header.id != header.id:
    print("Unmatched transaction")
    return None, None, None
  if header.rcode != RCODE.NOERROR:
    print("Query failed")
    return None, None, None

  # ==================== 2. Parse questions =========================
  # Despite beign unused, if I don't parse the questions there will be bufferOverflow.
  questions = [DNSQuestion.parse(buff) for _ in range(header.q)]
  del questions
  # ==================== 3. Parse answers ===========================
  answers = [RR.parse(buff) for _ in range(header.a)]   
  # ==================== 4. Parse authority =========================
  authorities = [RR.parse(buff) for _ in range(header.auth)]    
  # ==================== 5. Parse additionals =======================
  additional = [RR.parse(buff) for _ in range(header.ar)]

  #NOTE Unpacking doesn't work with None
  return answers, authorities, additional

def domainSplit(domain: str) -> list[str]: # IDK why i built this, I think it's neater.
  return domain.split(".")

if __name__ == '__main__':
  # Total mess of code, compounded by Ai assistence. Will clean up in commit soon.
  # Create a UDP socket
  sock = socket(AF_INET, SOCK_DGRAM)
  cache = Cache()
  clearScreen()
  
  while True:
    targetDomain = input("Enter a domain name (or type '.help' for commands): ")
    clearScreen()
    
    # Command handling
    match targetDomain:
      case ".exit":
        break
      case ".list":
        domains, ips = cache.list()

        if cache.length == 0:
          print("Cache is empty")
          continue

        for domain, ip in zip(domains, ips):
          print(f"Domain: {domain}\tIP: {ip}")
        continue
      case ".clear":
        cache.clear()
        print("Cache cleared")
        continue
      case ".remove":
        _ = input("Enter the domain to remove: ")
        if _ in cache.cache:
          cache.remove(_)
          print(f"Domain \"{_}\" removed")
        else:
          print(f"Domain \"{_}\" not found")
        continue
      case ".help":
        print(f"{BREAKLINE}Commands:\n.exit: Exit the program\n.list: List the cache\n.clear: Clear the cache\n.remove: Remove a domain from the cache\n.help: Display this message{BREAKLINE}")
        continue
      case ".get":
        _ = input("Enter the domain to get: ")
        if _ in cache.cache:
          print(f"Domain \"{_}\" found at {cache.get(_)}")
        else:
          print(f"Domain \"{_}\" not found")
        continue
      case _:
        # Checking for missplelled commands
        if not domainValidation(targetDomain): 
          print("Invalid domain or command: Try '.help' for more information.")
          continue

    # Split the domain substrings
    domainParts = domainSplit(targetDomain)
    domainLength = len(domainParts)
    currentServer = ROOT_SERVER

    for i in range(domainLength - 1, -1, -1):
      subdomain = ".".join(domainParts[i:]) # queries for the subdomain in reverse order
      
      #FIXME Request IPv4 for now, look into Ipv6 later. Maybe there's a way to ask before querying?
      result = get_dns_record(sock, subdomain, currentServer, "A")
      if result is None:
        print(f"Failed to get record for \"{subdomain}\"")
        continue
      answers, authorities, additional = result

      #TODO Handle None, None, None case

      for answer in answers:
        if answer.rtype == QTYPE.A or answer.rtype == QTYPE.AAAA:
          currentServer = str(answer.rdata)
          print(f"Address: {currentServer}")
        else:
          print(f"Unhandled record type: {answer.rtype}")
          break

      for authority in authorities:
        if authority.rtype == QTYPE.NS:
          currentServer = str(authority.rdata)
          #print(f"Name Server: {authority.rdata}")
        else:
          print(f"Unhandled record type: {authority.rtype}")
          break
    print(LONGSPACE)
    #cache.add(targetDomain, currentServer)
  sock.close()
