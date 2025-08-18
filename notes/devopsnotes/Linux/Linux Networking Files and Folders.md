# Linux Networking Files and Folders

## Core Network Configuration Files

### Essential Configuration Files
- **`/etc/hosts`**: Static hostname-to-IP mappings for local resolution
- **`/etc/resolv.conf`**: DNS resolver configuration (nameservers, search domains)
- **`/etc/hostname`**: System's hostname
- **`/etc/network/interfaces`**: Legacy network interface configuration (Debian-based)
- **`/etc/netplan/`**: Modern network configuration (Ubuntu 18.04+)
- **`/etc/hosts.allow`** and **`/etc/hosts.deny`**: TCP wrappers access control
- **`/etc/nsswitch.conf`**: Order of name service lookups (hosts, dns, etc.)
- **`/etc/sysctl.conf`**: Kernel network parameters (IP forwarding, etc.)

### Advanced Network Configuration
- **`/etc/iproute2/rt_tables`**: Routing table definitions for policy routing
- **`/etc/iptables/`**: Firewall rules storage directory
- **`/etc/ufw/`**: UFW (Uncomplicated Firewall) configuration
- **`/etc/networkmanager/`**: NetworkManager configuration
- **`/etc/wpa_supplicant/`**: Wi-Fi configuration files
- **`/etc/systemd/network/`**: systemd-networkd configuration files

## Network Interface Management

### Modern IP Command Usage

```bash
# Interface information and status
ip addr show                           # Display all interfaces
ip addr show eth0                      # Show specific interface
ip -4 addr show                        # IPv4 addresses only
ip -6 addr show                        # IPv6 addresses only
ip link show                          # Physical link information

# Interface management
ip link set eth0 up                    # Bring interface up
ip link set eth0 down                  # Bring interface down
ip addr add 192.168.1.100/24 dev eth0 # Add IP address
ip addr del 192.168.1.100/24 dev eth0 # Remove IP address

# Routing table management
ip route show                          # Display routing table
ip route show table all               # All routing tables
ip route add 192.168.2.0/24 via 192.168.1.1  # Add static route
ip route del 192.168.2.0/24           # Delete route
ip route get 8.8.8.8                  # Show route to destination
```

### Legacy ifconfig Commands

```bash
# Basic interface operations
ifconfig                               # Display all interfaces
ifconfig eth0                          # Show specific interface
ifconfig eth0 192.168.1.100/24         # Configure IP address
ifconfig eth0:1 192.168.1.101/24       # Create virtual interface
ifconfig eth0 down                     # Disable interface
ifconfig eth0 up                       # Enable interface
```

## Network Connectivity Testing

### Ping and Connectivity Tests

```bash
# Basic connectivity testing
ping -c 4 google.com                   # Send 4 packets
ping -i 0.2 -c 10 server               # 200ms interval between packets
ping -s 1472 server                    # Test with large packet size (MTU)
ping6 ipv6.google.com                  # IPv6 ping test
ping -I eth0 8.8.8.8                  # Ping from specific interface

# Advanced ping options
ping -f 8.8.8.8                       # Flood ping (requires root)
ping -W 5 server                       # Set timeout to 5 seconds
ping -D server                        # Print timestamps
```

### Network Path Analysis

```bash
# Traceroute variations
traceroute google.com                  # Show network path (UDP)
traceroute -I google.com               # Use ICMP packets
traceroute -T -p 80 google.com        # TCP traceroute to specific port
traceroute6 ipv6.google.com           # IPv6 traceroute
mtr google.com                         # Continuous traceroute with statistics
```

## Port and Service Testing

### Network Connectivity Tools

```bash
# netcat (nc) - Network Swiss Army Knife
nc -zv server 80                       # Test TCP port connectivity
nc -zv -w 5 server 22                 # Test with 5-second timeout
nc -u -zv server 53                   # Test UDP port (DNS)
nc -l 8080                             # Listen on port 8080
echo "GET / HTTP/1.1\r\nHost: example.com\r\n\r\n" | nc server 80

# telnet for protocol testing
telnet smtp.gmail.com 587              # Test SMTP connection
telnet pop.gmail.com 995               # Test POP3 connection
telnet imap.gmail.com 993              # Test IMAP connection

# nmap for port scanning
nmap -p 80,443 server                  # Scan specific ports
nmap -sS -O server                     # SYN scan with OS detection
nmap -sU -p 53,67,68 server           # UDP port scan
```

## Service Discovery and Monitoring

### Socket Statistics (ss) - Modern netstat

```bash
# Basic socket information
ss -tuln                               # TCP/UDP listening ports
ss -tulpn                              # Include process names
ss -an | grep :80                      # Filter connections on port 80
ss -s                                  # Summary statistics

# Advanced filtering
ss 'sport = :ssh'                      # SSH server connections
ss 'dport = :80'                       # HTTP client connections
ss 'state connected'                   # Only established connections
ss 'src 192.168.1.0/24'              # Connections from subnet
```

### Legacy netstat Commands

```bash
# Basic network statistics
netstat -tuln                          # Listening TCP/UDP ports
netstat -i                             # Network interface statistics
netstat -r                             # Routing table
netstat -c                             # Continuous output
netstat -p                             # Show process names
```

## DNS Management and Resolution

### DNS Query Tools

```bash
# dig - Domain Information Groper
dig google.com                         # Basic A record lookup
dig @8.8.8.8 google.com               # Query specific DNS server
dig google.com MX                      # Mail exchange records
dig google.com AAAA                    # IPv6 address (AAAA record)
dig +short google.com                  # Brief output format
dig +trace google.com                  # Show full DNS resolution path
dig -x 8.8.8.8                        # Reverse DNS lookup

# nslookup (legacy but still used)
nslookup google.com                    # Basic lookup
nslookup google.com 8.8.8.8           # Use specific DNS server
nslookup -type=MX google.com          # Query specific record type

# host command (simple)
host google.com                        # Simple DNS lookup
host -t MX google.com                  # Specific record type
host -a google.com                     # All record types
```

### DNS Configuration Files

```bash
# /etc/hosts - Local hostname resolution
127.0.0.1       localhost
127.0.1.1       hostname.localdomain hostname
192.168.1.100   server.local server
::1             localhost ip6-localhost ip6-loopback

# /etc/resolv.conf - DNS server configuration
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
search local.domain company.com
options timeout:2 attempts:3 rotate

# /etc/nsswitch.conf - Name resolution order
hosts: files dns myhostname
networks: files
protocols: db files
services: db files
ethers: db files
rpc: db files
```

## HTTP/HTTPS Network Tools

### curl - Advanced HTTP Client

```bash
# Basic HTTP operations
curl https://api.example.com           # Simple GET request
curl -X POST https://api.example.com   # POST request
curl -H "Content-Type: application/json" -d '{"key":"value"}' api.url
curl -H "Authorization: Bearer $TOKEN" https://api.com

# DevOps common patterns
curl -I https://site.com               # Headers only (HEAD request)
curl -L https://bit.ly/shorturl        # Follow redirects
curl -k https://self-signed.com        # Ignore SSL certificate errors
curl -w "%{http_code}\n" -o /dev/null -s https://site.com  # Status code only
curl -w "@curl-format.txt" https://site.com  # Custom output format

# Authentication and session management
curl -u username:password https://api.com     # Basic authentication
curl -b cookies.txt -c cookies.txt https://site.com  # Cookie handling
curl --digest -u user:pass https://api.com    # Digest authentication

# File operations
curl -O https://site.com/file.tar.gz   # Download with original filename
curl -o myfile.tar.gz https://site.com/archive.tar.gz  # Custom filename
curl -T localfile.txt ftp://server/    # Upload file via FTP
curl -F "file=@upload.txt" https://httpbin.org/post  # Form upload
```

### wget - Web File Downloader

```bash
# Basic download operations
wget https://example.com/file.tar.gz
wget -O newname.tar.gz https://example.com/file.tar.gz
wget -c https://example.com/largefile.iso  # Continue interrupted download
wget -t 3 https://example.com/file.tar.gz  # Retry 3 times on failure

# Recursive downloading
wget -r -np -k https://site.com/docs/   # Mirror directory structure
wget --mirror --convert-links https://site.com/  # Full site mirror
wget -r -l 2 -A "*.pdf" https://site.com/  # Download PDFs, 2 levels deep
```

## Network Monitoring and Analysis

### Network Statistics and Monitoring

```bash
# Interface statistics
cat /proc/net/dev                      # Network interface statistics
ip -s link show                       # Interface statistics via ip command
ethtool eth0                          # Ethernet interface information
ethtool -S eth0                       # Detailed interface statistics

# Network connections monitoring
watch -n 1 'ss -tuln'                 # Monitor listening ports
watch -n 2 'ss -i'                    # Monitor interface statistics
lsof -i                               # List all network connections
lsof -i :80                           # Connections on specific port
```

### Packet Capture and Analysis

```bash
# tcpdump - Command-line packet analyzer
tcpdump -i eth0                       # Capture on specific interface
tcpdump -i any                        # Capture on all interfaces
tcpdump -i eth0 port 80               # HTTP traffic only
tcpdump -i eth0 -w capture.pcap       # Save capture to file
tcpdump -r capture.pcap               # Read from saved file

# Advanced tcpdump filters
tcpdump 'host 192.168.1.100'         # Traffic to/from specific host
tcpdump 'net 192.168.1.0/24'         # Traffic to/from network range
tcpdump 'port 53 or port 80'         # DNS or HTTP traffic
tcpdump 'tcp[tcpflags] & (tcp-syn) != 0'  # TCP SYN packets only
tcpdump -A 'port 80'                  # Show packet content (ASCII)
```

## Firewall Management

### iptables - Advanced Firewall Rules

```bash
# View and manage rules
iptables -L                            # List all rules
iptables -L -n -v                      # Numeric output with packet counts
iptables -t nat -L                     # NAT table rules

# Basic rule management
iptables -A INPUT -p tcp --dport 22 -j ACCEPT    # Allow SSH
iptables -A INPUT -p tcp --dport 80 -j ACCEPT    # Allow HTTP
iptables -A INPUT -p tcp --dport 443 -j ACCEPT   # Allow HTTPS
iptables -A INPUT -j DROP                        # Default drop policy

# Advanced rules
iptables -A INPUT -s 192.168.0.0/16 -j ACCEPT   # Allow private networks
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT  # Connection tracking
iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT  # Rate limiting

# Save and restore rules
iptables-save > /etc/iptables/rules.v4
iptables-restore < /etc/iptables/rules.v4
```

### UFW - Uncomplicated Firewall

```bash
# Basic UFW operations
ufw enable                             # Enable firewall
ufw disable                            # Disable firewall
ufw status                             # Show current status
ufw status verbose                     # Detailed status
ufw --force reset                      # Reset to defaults

# Rule management
ufw allow 22                           # Allow SSH port
ufw allow ssh                          # Allow SSH by service name
ufw allow 80/tcp                       # Allow HTTP (TCP only)
ufw allow from 192.168.1.0/24          # Allow from subnet
ufw allow from 192.168.1.100 to any port 22  # Specific source to SSH
ufw limit ssh                          # Rate limit SSH connections
ufw deny 23                            # Deny telnet

# Application profiles
ufw app list                           # List available profiles
ufw allow 'Apache Full'               # Allow Apache HTTP and HTTPS
ufw allow 'OpenSSH'                   # Allow OpenSSH
```

## Network Troubleshooting

### Connectivity Debugging

```bash
# Multi-level connectivity testing
ping -c 4 127.0.0.1                   # Test loopback
ping -c 4 $(ip route | grep default | awk '{print $3}')  # Test gateway
ping -c 4 8.8.8.8                     # Test external connectivity
ping -c 4 google.com                  # Test DNS resolution

# Interface debugging
ip link show                          # Check physical link status
ethtool eth0                          # Check link speed and duplex
mii-tool eth0                         # Alternative link status tool
```

### Advanced Network Analysis

```bash
# Bandwidth testing
iperf3 -s                             # Start iperf3 server
iperf3 -c server_ip                   # Connect as client
iperf3 -c server_ip -u               # UDP test
iperf3 -c server_ip -t 60            # 60-second test

# Network latency analysis
mtr -r -c 10 google.com               # Generate report with 10 cycles
hping3 -S -p 80 -c 5 google.com      # Custom packet testing
```

This comprehensive guide covers all essential Linux networking concepts, tools, and configuration files needed for effective DevOps network management and troubleshooting.