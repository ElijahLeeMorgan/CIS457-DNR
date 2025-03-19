# CIS457-DNR

Elijah Morgan\
CIS 457 02

# Domain Name Resolver

![Ethernet Switch](img/switch.jpg)

The second project for CIS457: Data Communications.
DNR is a simple UDP-based iterative DNS client written in Python3. Unlike the first project [NUSA](https://github.com/ElijahLeeMorgan/CIS457-NUSA) this application will interact on WAN with other DNS servers. However, it will not take DNS requests, only send them.

[Outline of project requirements and expectations.](https://dulimarta-teaching.netlify.app/cs457/p2-iterative-dns.html)



## Required Features

* Implement an iterative domain name resolver in Python (3.12 or newer). Your code shall be designed to use while loop(s) that send DNS messages and parse their corresponding responses. 
  * Avoid code bloat as the result of copying chunk of code multiple times. Instead, organize them into function(s).

* RFC 1034 specifies that the protocol can be implemented using either TCP or UDP. For this assignment, your client shall use a UDP socket. 
  * Specifically, create only one socket, design the program to run in a loop prompting the user to enter domain name. The loop stops when the user types .exit

* Your client shall print the following informational output:
  * Which TLD name server(s) are consulted, whether it is obtained from the cache or from a root server
  * Which Authoritative name server(s) are consulted, whether it is obtained from the cache or from a TLD name server
  * The IP address resolution of the domain name in question, whether it is obtained from the cache from from an authoritative name server
  * When a domain name has an alias

* Your client shall print sufficient error message when the user queried a non-existing domains

* When the user types a domain which has an associated alias, your client shall continue to "follow" the alias until it eventually resolves to an IP address.
  * Your client should be designed to handle theoretically unlimited chain of aliases.

* Add additional logic to consult alternative name servers if one shows no response after a timeout interval

* Use appropriate Python data structures (dictionary/map) to implement caching strategy that stores both the name servers address and the resolved IP addresses.
  * Use the .list command to show cache. The output should be numbered starting from 1, the number will be used by the .remove command below
  * Use the .clear to remove all cache copy
  * Use the .remove N to delete a specific cache copy where N is an integer shown in the .list output above. Implement error handling when the user attempts to remove non-existing cache copy (N is non-positive or too big)
* IP addresses shall be displayed in dot-decimal notation i.e. 175.23.28.184

### Extra Credit
* (2 pts) In addition to resolving to IPv4 address(es), also resolve the domain name to IPv6 address(es)
* (3 pts) When multiple name servers are available and one of the servers is non-responsive, resend queries to alternate name servers exhaustively
* (4-8 points) Implement the iterative domain name resolver without any external DNS module (dnslib, dnspython, ...)
