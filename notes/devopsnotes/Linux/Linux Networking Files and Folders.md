-  /etc/hosts: static hostname-to-IP mappings  
- /etc/resolv.conf: DNS resolver configuration (nameservers)  
- /etc/hostname: system's hostname  	
- /etc/network/interfaces: legacy interface configuration (Debian-based)  	
- /etc/netplan/: modern network config (used in Ubuntu 18.04+)  
- /etc/hosts.allow and /etc/hosts.deny: TCP wrappers access control  
- /etc/nsswitch.conf: order of name service lookups (hosts, dns, etc.)  
- /etc/sysctl.conf: kernel network parameters (e.g., IP forwarding)  
- /etc/iproute2/rt_tables: routing table definitions  
- /etc/iptables/: firewall rules (if saved)  
- /etc/networkmanager/: NetworkManager settings  
- /etc/wpa_supplicant/: Wi-Fi configuration files