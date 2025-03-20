from dnslib import DNSRecord, DNSHeader, DNSBuffer, DNSQuestion, RR, QTYPE, RCODE
from socket import socket, SOCK_DGRAM, AF_INET
from os import system, name

"""
Elijah Morgan
CIS 457 02
"""

# There are 13 root servers defined at https://www.iana.org/domains/root/servers
IPv4_ROOT_SERVERS = (
    "198.41.0.4",      # a.root-servers.net
    "199.9.14.201",    # b.root-servers.net
    "192.33.4.12",     # c.root-servers.net
    "199.7.91.13",     # d.root-servers.net
    "192.203.230.10",  # e.root-servers.net
    "192.5.5.241",     # f.root-servers.net
    "192.112.36.4",    # g.root-servers.net
    "198.97.190.53",   # h.root-servers.net
    "192.36.148.17",   # i.root-servers.net
    "192.58.128.30",   # j.root-servers.net
    "193.0.14.129",    # k.root-servers.net
    "199.7.83.42",     # l.root-servers.net
    "202.12.27.33"     # m.root-servers.net
)
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
  #print(LONGSPACE, "DNS query", repr(q))
  udp_socket.sendto(q.pack(), (parent_server, DNS_PORT))
  pkt, _ = udp_socket.recvfrom(8192)
  buff = DNSBuffer(pkt)
  
  # A/AAAA queries typically return information in the answer section.
  # NS queries typically return information in the authority section.
  answers = []
  authorities = []
  additional = []
  
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

  return answers, authorities, additional

def parseAnswer(sock:socket, cache:Cache, answers: RR) -> str:
  # Check for answers
  for answer in answers:
    if (answer.rtype == QTYPE.A): # or (answer.rtype == QTYPE.AAAA): #TODO IpV6 for extra credit
      ip = str(answer.rdata)
      print(f"Domain resolved to: {ip}")
      return ip
    elif answer.rtype == QTYPE.CNAME:
      alias = str(answer.rdata)
      print(f"Alias: {alias}")
      return query(sock, cache, alias, IPv4_ROOT_SERVERS)
    else:
      print(f"Unhandled record type: {answer.rtype}")
  
def parseNameServers(sock:socket, cache:Cache, authorities: RR, additionals:RR, targetDomain:str) -> str:
  # Check for server aliases
  visited = set()

  if authorities is None:
    print(f"No authority for \"{targetDomain}\"")
  else:
    # Parse the name servers
    nameServers = [str(auth.rdata) for auth in authorities if auth.rtype == QTYPE.NS]
    additional_map = {str(add.rname): str(add.rdata) for add in additionals if add.rtype == QTYPE.A}

    for ns in nameServers:
      # AI Assisted code below
      if ns in additional_map and additional_map[ns] not in visited:
        visited.add(additional_map[ns])
        print(f"Name Server: {ns} at {additional_map[ns]}\n")
        ip = query(sock, cache, targetDomain, [additional_map[ns]])
        if ip:
          return ip
      elif ns not in additional_map:
        # Resolve the name server recursively if its IP is not in the additional section
        print(f"Resolving IP for Name Server: {ns}")
        ns_ip = query(sock, cache, ns)
        if ns_ip and ns_ip not in visited:
          visited.add(ns_ip)
          ip = query(sock, cache, targetDomain, [ns_ip])
          if ip:
            return ip
    print(f"Failure to resolve: \"{targetDomain}\"\nPlease check your network connection.")  

# Runs query() based on user input
def inputLoop(sock:socket, cache:Cache):
  while True:
    targetDomain = input("Enter a domain name (or type '.help' for commands): ")
    clearScreen()
    
    # Command handling
    match targetDomain.lower():
      case ".exit":
        break
      case ".list":
        domains, ips = cache.list()

        if cache.length == 0:
          print("Cache is empty")
          continue

        for domain, ip in zip(domains, ips):
          print(f"Domain: {domain}\tIP: {ip}")
      case ".clear":
        cache.clear()
        print("Cache cleared")
      case ".remove":
        _ = input("Enter the domain to remove: ")
        if _ in cache.cache:
          cache.remove(_)
          print(f"Domain \"{_}\" removed")
        else:
          print(f"Domain \"{_}\" not found")
      case ".help":
        print(f"{BREAKLINE}Commands:\n.exit: Exit the program\n.list: List the cache\n.clear: Clear the cache\n.remove: Remove a domain from the cache\n.help: Display this message{BREAKLINE}")
      case ".get":
        _ = input("Enter the domain to get: ")
        if _ in cache.cache:
          print(f"Domain \"{_}\" found at {cache.get(_)}")
        else:
          print(f"Domain \"{_}\" not found")
      case _:
        # Checking for missplelled commands
        if not domainValidation(targetDomain): 
          print("Invalid domain or command: Try '.help' for more information.")
        else:
          ip = query(sock=sock, cache=cache, targetDomain=targetDomain) # Root servers are fine

def query(sock:socket, cache:Cache, targetDomain:str, parentServers:list[str] = IPv4_ROOT_SERVERS) -> str:  
  # Check cache
  if targetDomain in cache.cache:
    print(f"Domain \"{targetDomain}\" resolved in cache: {cache.get(targetDomain)}")
    return cache.get(targetDomain)

  for parent in parentServers:
    answers, authorities, additionals = get_dns_record(sock, targetDomain, parent, "A")

    if (answers is None) or (len(answers) <= 0):
      print(f"No answer for \"{targetDomain}\" at \"{parent}\"")
    else:
      # There should be some kind of answer
      ans = parseAnswer(sock, cache, answers)
      if ans is not None:
        cache.add(targetDomain, ans)
        return ans
    ip = parseNameServers(sock, cache, authorities, additionals, targetDomain)
    if ip is not None:
      return ip
    parseNameServers(sock, cache, authorities, additionals, targetDomain)
  print(WEAKLINE)

def main():
  c = Cache()
  # Create a UDP socket
  s = socket(AF_INET, SOCK_DGRAM)
  # Get the domain name / command from the user
  inputLoop(s, c)

  # Close the socket, no reason to use multiple sockets.
  s.close()

if __name__ == '__main__':
  main()