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
LONGSPACE = "\n" * 3

def clearScreen() -> None:
  system('cls' if name == 'nt' else 'clear')

def get_dns_record(udp_socket, domain:str, parent_server: str, record_type) -> list[RR]:
  q = DNSRecord.question(domain, qtype = record_type)
  q.header.rd = 0   # Recursion Desired?  NO
  #print(BREAKLINE, "DNS query", repr(q))
  udp_socket.sendto(q.pack(), (parent_server, DNS_PORT))
  pkt, _ = udp_socket.recvfrom(8192)
  buff = DNSBuffer(pkt)
  
  # A/AAAA queries typically return information in the answer section.
  # NS queries typically return information in the authority section.
  answers = []
  authorities = []
  #additional = []

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
  
  # Parse header section #1
  header = DNSHeader.parse(buff)
  #print("DNS header", repr(header), WEAKLINE)
  if q.header.id != header.id:
    print("Unmatched transaction")
    return
  if header.rcode != RCODE.NOERROR:
    print("Query failed")
    return None

  # Parse the question section #2
  for k in range(header.q):
    q = DNSQuestion.parse(buff)
    print(f"Question-{k} {repr(q)}\t\tParent-Server: {parent_server}{WEAKLINE}")

  # Parse the answer section #3
  for k in range(header.a):
    a = RR.parse(buff)
    #print(f"Answer-{k} {repr(a)}")
    answers.append(a)
    #if a.rtype == QTYPE.A:
      #print("IP address")
      
  # Parse the authority section #4
  for k in range(header.auth):
    auth = RR.parse(buff)
    #print(f"Authority-{k} {repr(auth)}")
    authorities.append(auth)
      
  # Parse the additional section #5
  for k in range(header.ar):
    adr = RR.parse(buff)

  #NOTE Unpacking doesn't work with None
  return answers, authorities

def domainSplit(domain: str) -> list[str]: # IDK why i built this, I think it's neater.
  return domain.split(".")

if __name__ == '__main__':
  # Total mess of code, compounded by Ai assistence. Will clean up in commit soon.
  # Create a UDP socket
  sock = socket(AF_INET, SOCK_DGRAM)
  clearScreen()
  
  while True:
    targetDomain = input("Enter a domain name (or type '.exit' to quit): ")
    clearScreen()
    if targetDomain == ".exit":
      break

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
      answers, authorities = result

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
    print(BREAKLINE)
  sock.close()
