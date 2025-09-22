# Linux Security Firewall Network Security

**Firewall and network security** protects systems through packet filtering, intrusion detection, network monitoring, and comprehensive traffic control using iptables, firewalld, and security tools.

## Advanced Firewall Configuration

### iptables Comprehensive Security Rules

#### Production iptables Ruleset
```bash
#!/bin/bash
# iptables-security-setup.sh

# Comprehensive iptables security configuration
setup_iptables_security() {
    echo "Setting up iptables security rules..."

    # Clear existing rules
    iptables -F
    iptables -X
    iptables -t nat -F
    iptables -t nat -X
    iptables -t mangle -F
    iptables -t mangle -X
    iptables -t raw -F
    iptables -t raw -X

    # Set default policies (deny all)
    iptables -P INPUT DROP
    iptables -P FORWARD DROP
    iptables -P OUTPUT ACCEPT

    # Allow loopback traffic
    iptables -A INPUT -i lo -j ACCEPT
    iptables -A OUTPUT -o lo -j ACCEPT

    # Allow established and related connections
    iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

    # Anti-spoofing rules (adjust interface as needed)
    iptables -A INPUT -s 10.0.0.0/8 -i eth0 -j DROP
    iptables -A INPUT -s 169.254.0.0/16 -i eth0 -j DROP
    iptables -A INPUT -s 172.16.0.0/12 -i eth0 -j DROP
    iptables -A INPUT -s 192.168.0.0/16 -i eth0 -j DROP
    iptables -A INPUT -s 224.0.0.0/4 -i eth0 -j DROP
    iptables -A INPUT -d 224.0.0.0/4 -i eth0 -j DROP
    iptables -A INPUT -s 240.0.0.0/5 -i eth0 -j DROP
    iptables -A INPUT -d 240.0.0.0/5 -i eth0 -j DROP
    iptables -A INPUT -s 0.0.0.0/8 -i eth0 -j DROP
    iptables -A INPUT -d 0.0.0.0/8 -i eth0 -j DROP
    iptables -A INPUT -d 239.255.255.0/24 -i eth0 -j DROP
    iptables -A INPUT -d 255.255.255.255 -i eth0 -j DROP

    # Drop fragmented packets
    iptables -A INPUT -f -j DROP

    # Drop invalid packets
    iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

    # Rate limiting for SSH (prevent brute force)
    iptables -A INPUT -p tcp --dport 2222 -m conntrack --ctstate NEW -m recent --set --name SSH
    iptables -A INPUT -p tcp --dport 2222 -m conntrack --ctstate NEW -m recent --update --seconds 60 --hitcount 4 --name SSH -j DROP

    # Allow SSH from specific networks only
    iptables -A INPUT -p tcp -s 192.168.1.0/24 --dport 2222 -j ACCEPT
    iptables -A INPUT -p tcp -s 10.0.0.0/8 --dport 2222 -j ACCEPT

    # Web services (HTTP/HTTPS)
    iptables -A INPUT -p tcp --dport 80 -j ACCEPT
    iptables -A INPUT -p tcp --dport 443 -j ACCEPT

    # Monitoring services (restricted access)
    iptables -A INPUT -p tcp -s 192.168.1.100 --dport 9100 -j ACCEPT  # Node exporter
    iptables -A INPUT -p tcp -s 192.168.1.100 --dport 9113 -j ACCEPT  # Nginx exporter

    # DNS (outbound only)
    iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
    iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

    # NTP (outbound only)
    iptables -A OUTPUT -p udp --dport 123 -j ACCEPT

    # ICMP rules (limited)
    iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT
    iptables -A INPUT -p icmp --icmp-type echo-reply -j ACCEPT
    iptables -A INPUT -p icmp --icmp-type destination-unreachable -j ACCEPT
    iptables -A INPUT -p icmp --icmp-type time-exceeded -j ACCEPT

    # Log dropped packets (limited to prevent log flooding)
    iptables -A INPUT -m limit --limit 5/min -j LOG --log-prefix "iptables denied: " --log-level 7

    # Final drop rule
    iptables -A INPUT -j DROP

    echo "iptables rules applied successfully"
}

# Save and restore iptables rules
save_iptables_rules() {
    # Create iptables directory
    mkdir -p /etc/iptables

    # Save current rules
    iptables-save > /etc/iptables/rules.v4
    ip6tables-save > /etc/iptables/rules.v6

    # Create systemd service for rule restoration
    cat << 'EOF' > /etc/systemd/system/iptables-restore.service
[Unit]
Description=Restore iptables rules
Before=network-pre.target
Wants=network-pre.target

[Service]
Type=oneshot
ExecStart=/sbin/iptables-restore /etc/iptables/rules.v4
ExecStartPost=/sbin/ip6tables-restore /etc/iptables/rules.v6

[Install]
WantedBy=multi-user.target
EOF

    systemctl enable iptables-restore.service
    echo "iptables rules saved and auto-restore configured"
}

# Execute setup
setup_iptables_security
save_iptables_rules
```

#### iptables Management Script
```bash
#!/bin/bash
# iptables-manager.sh

RULES_FILE="/etc/iptables/rules.v4"

case "$1" in
    status)
        echo "=== Current iptables rules ==="
        iptables -L -n -v --line-numbers
        ;;

    save)
        iptables-save > "$RULES_FILE"
        echo "Rules saved to $RULES_FILE"
        ;;

    restore)
        if [[ -f "$RULES_FILE" ]]; then
            iptables-restore < "$RULES_FILE"
            echo "Rules restored from $RULES_FILE"
        else
            echo "No saved rules found"
        fi
        ;;

    block)
        if [[ -n "$2" ]]; then
            iptables -I INPUT -s "$2" -j DROP
            echo "Blocked IP: $2"
        else
            echo "Usage: $0 block <IP_ADDRESS>"
        fi
        ;;

    unblock)
        if [[ -n "$2" ]]; then
            iptables -D INPUT -s "$2" -j DROP 2>/dev/null && echo "Unblocked IP: $2" || echo "IP not found in block list"
        else
            echo "Usage: $0 unblock <IP_ADDRESS>"
        fi
        ;;

    list-blocked)
        echo "=== Blocked IPs ==="
        iptables -L INPUT -n | grep DROP | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}'
        ;;

    reset)
        iptables -F
        iptables -X
        iptables -P INPUT ACCEPT
        iptables -P FORWARD ACCEPT
        iptables -P OUTPUT ACCEPT
        echo "iptables rules reset to defaults"
        ;;

    *)
        echo "Usage: $0 {status|save|restore|block|unblock|list-blocked|reset}"
        exit 1
        ;;
esac
```

### firewalld Configuration (RHEL/CentOS)

#### Advanced firewalld Setup
```bash
# Install and enable firewalld
dnf install firewalld
systemctl enable --now firewalld

# Basic firewalld configuration
firewall-cmd --set-default-zone=public
firewall-cmd --permanent --zone=public --set-target=DROP

# Configure zones
firewall-cmd --permanent --new-zone=trusted-internal
firewall-cmd --permanent --zone=trusted-internal --set-target=ACCEPT
firewall-cmd --permanent --zone=trusted-internal --add-source=192.168.1.0/24

firewall-cmd --permanent --new-zone=dmz-servers
firewall-cmd --permanent --zone=dmz-servers --set-target=DROP
firewall-cmd --permanent --zone=dmz-servers --add-source=10.0.1.0/24

# Service configuration
firewall-cmd --permanent --zone=public --add-service=ssh
firewall-cmd --permanent --zone=public --add-service=http
firewall-cmd --permanent --zone=public --add-service=https

# Custom services
firewall-cmd --permanent --new-service=monitoring
firewall-cmd --permanent --service=monitoring --set-description="Monitoring services"
firewall-cmd --permanent --service=monitoring --add-port=9100/tcp
firewall-cmd --permanent --service=monitoring --add-port=9113/tcp

firewall-cmd --permanent --zone=trusted-internal --add-service=monitoring

# Port configurations
firewall-cmd --permanent --zone=public --add-port=2222/tcp  # Custom SSH port

# Rich rules for advanced filtering
firewall-cmd --permanent --zone=public --add-rich-rule='rule family="ipv4" source address="192.168.1.100" service name="ssh" accept'
firewall-cmd --permanent --zone=public --add-rich-rule='rule family="ipv4" source address="0.0.0.0/0" service name="ssh" reject'

# Rate limiting
firewall-cmd --permanent --zone=public --add-rich-rule='rule family="ipv4" service name="ssh" accept limit value="3/m"'

# Reload configuration
firewall-cmd --reload

# Check configuration
firewall-cmd --list-all-zones
```

## Intrusion Detection and Prevention

### Fail2ban Configuration

#### Comprehensive Fail2ban Setup
```bash
# Install fail2ban
apt install fail2ban -y  # Debian/Ubuntu
dnf install fail2ban -y  # RHEL/CentOS/Fedora

# Main configuration: /etc/fail2ban/jail.local
cat << 'EOF' > /etc/fail2ban/jail.local
[DEFAULT]
# Ban settings
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

# Communication
destemail = security@company.com
sendername = Fail2Ban-%(fq-hostname)s
mta = sendmail

# Actions (ban and send email)
action = %(action_mwl)s

# Ignore trusted IPs
ignoreip = 127.0.0.1/8 192.168.1.0/24 10.0.0.0/8

[sshd]
enabled = true
port = 2222
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600

[sshd-ddos]
enabled = true
port = 2222
filter = sshd-ddos
logpath = /var/log/auth.log
maxretry = 6
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 1800

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 5
bantime = 1800

[nginx-badbots]
enabled = true
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2
bantime = 86400

[postfix]
enabled = true
filter = postfix
logpath = /var/log/mail.log
maxretry = 3
bantime = 3600

[dovecot]
enabled = true
filter = dovecot
logpath = /var/log/mail.log
maxretry = 3
bantime = 3600

[apache-auth]
enabled = false
filter = apache-auth
logpath = /var/log/apache*/*error.log
maxretry = 3

[apache-badbots]
enabled = false
filter = apache-badbots
logpath = /var/log/apache*/*access.log
maxretry = 2
bantime = 86400

[recidive]
enabled = true
filter = recidive
logpath = /var/log/fail2ban.log
action = %(action_mwl)s
bantime = 86400
findtime = 86400
maxretry = 3
EOF

# Custom filters
cat << 'EOF' > /etc/fail2ban/filter.d/nginx-badbots.conf
[Definition]
failregex = ^<HOST> -.*"(GET|POST|HEAD).*HTTP.*" (404|444) .*$
            ^<HOST> -.*"(GET|POST|HEAD).*(\.php|\.asp|\.exe|\.pl|\.cgi|\.scgi).*HTTP.*" .*$
ignoreregex =
EOF

cat << 'EOF' > /etc/fail2ban/filter.d/custom-app.conf
[Definition]
failregex = ^<HOST> - - \[.*\] "(GET|POST|HEAD)" .* (401|403|404) .*$
            ^.*authentication failure.*rhost=<HOST>.*$
ignoreregex =
EOF

# Enable and start fail2ban
systemctl enable fail2ban
systemctl start fail2ban

echo "Fail2ban configured and started"
```

#### Fail2ban Management Script
```bash
#!/bin/bash
# fail2ban-manager.sh

case "$1" in
    status)
        echo "=== Fail2ban Status ==="
        fail2ban-client status
        ;;

    jail-status)
        if [[ -n "$2" ]]; then
            fail2ban-client status "$2"
        else
            echo "Usage: $0 jail-status <jail_name>"
            echo "Available jails:"
            fail2ban-client status | grep "Jail list" | cut -d: -f2 | tr ',' '\n' | xargs
        fi
        ;;

    unban)
        if [[ -n "$2" && -n "$3" ]]; then
            fail2ban-client set "$2" unbanip "$3"
            echo "Unbanned $3 from jail $2"
        else
            echo "Usage: $0 unban <jail_name> <ip_address>"
        fi
        ;;

    ban)
        if [[ -n "$2" && -n "$3" ]]; then
            fail2ban-client set "$2" banip "$3"
            echo "Banned $3 in jail $2"
        else
            echo "Usage: $0 ban <jail_name> <ip_address>"
        fi
        ;;

    banned-ips)
        echo "=== Currently Banned IPs ==="
        for jail in $(fail2ban-client status | grep "Jail list" | cut -d: -f2 | tr ',' ' '); do
            banned=$(fail2ban-client status "$jail" | grep "Banned IP list" | cut -d: -f2 | xargs)
            if [[ -n "$banned" ]]; then
                echo "Jail: $jail"
                echo "  Banned IPs: $banned"
            fi
        done
        ;;

    reload)
        fail2ban-client reload
        echo "Fail2ban configuration reloaded"
        ;;

    logs)
        echo "=== Recent Fail2ban Logs ==="
        tail -n 50 /var/log/fail2ban.log
        ;;

    *)
        echo "Usage: $0 {status|jail-status|unban|ban|banned-ips|reload|logs}"
        echo ""
        echo "Examples:"
        echo "  $0 status"
        echo "  $0 jail-status sshd"
        echo "  $0 unban sshd 192.168.1.100"
        echo "  $0 ban sshd 192.168.1.200"
        exit 1
        ;;
esac
```

## Network Monitoring and Security

### Port Scanning Detection
```bash
#!/bin/bash
# port-scan-detector.sh

LOG_FILE="/var/log/port-scan-detection.log"
ALERT_EMAIL="security@company.com"

detect_port_scans() {
    echo "=== Port Scan Detection ==="

    # Check for multiple connection attempts from same IP
    netstat -tuln | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -nr | head -10 | \
    while read count ip; do
        if [[ $count -gt 20 && "$ip" != "127.0.0.1" && "$ip" != "0.0.0.0" ]]; then
            echo "$(date): Possible port scan from $ip ($count connections)" | tee -a "$LOG_FILE"
            echo "Possible port scan detected from $ip" | mail -s "Port Scan Alert" "$ALERT_EMAIL"
        fi
    done

    # Check for SYN flood attempts
    ss -tuln | grep SYN-RECV | wc -l | \
    while read syn_count; do
        if [[ $syn_count -gt 50 ]]; then
            echo "$(date): Possible SYN flood attack ($syn_count SYN-RECV)" | tee -a "$LOG_FILE"
            echo "Possible SYN flood attack detected" | mail -s "SYN Flood Alert" "$ALERT_EMAIL"
        fi
    done
}

# Monitor network connections
monitor_connections() {
    echo "=== Active Network Connections ==="
    echo "TCP Connections:"
    ss -tuln | grep tcp | wc -l

    echo "UDP Connections:"
    ss -tuln | grep udp | wc -l

    echo "Listening Services:"
    ss -tuln | grep LISTEN

    echo "Top Connection Sources:"
    ss -tun | awk '{print $6}' | cut -d: -f1 | sort | uniq -c | sort -nr | head -5
}

# Run monitoring
detect_port_scans
monitor_connections
```

### Network Traffic Analysis
```bash
#!/bin/bash
# network-traffic-analyzer.sh

INTERFACE="${1:-eth0}"
DURATION="${2:-60}"
OUTPUT_FILE="/tmp/network-analysis-$(date +%Y%m%d-%H%M%S).txt"

analyze_traffic() {
    echo "=== Network Traffic Analysis ==="
    echo "Interface: $INTERFACE"
    echo "Duration: $DURATION seconds"
    echo "Output: $OUTPUT_FILE"

    {
        echo "Network Traffic Analysis Report"
        echo "Generated: $(date)"
        echo "Interface: $INTERFACE"
        echo "Duration: $DURATION seconds"
        echo ""

        # Capture traffic statistics
        echo "=== Interface Statistics ==="
        cat /proc/net/dev | grep "$INTERFACE"

        echo ""
        echo "=== Active Connections ==="
        ss -tuln | head -20

        echo ""
        echo "=== Top Processes by Network Usage ==="
        lsof -i | head -20

        echo ""
        echo "=== Network Configuration ==="
        ip addr show "$INTERFACE"
        ip route show

    } > "$OUTPUT_FILE"

    echo "Analysis completed. Report saved to: $OUTPUT_FILE"
}

# DDoS detection
detect_ddos() {
    echo "=== DDoS Detection ==="

    # Check for excessive connections
    CONN_COUNT=$(ss -tun | wc -l)
    if [[ $CONN_COUNT -gt 1000 ]]; then
        echo "WARNING: High connection count detected: $CONN_COUNT"

        # Find top connection sources
        echo "Top connection sources:"
        ss -tun | awk '{print $6}' | cut -d: -f1 | sort | uniq -c | sort -nr | head -10

        # Alert
        echo "Possible DDoS attack detected on $(hostname)" | \
        mail -s "DDoS Alert - High Connection Count" security@company.com
    fi

    # Check bandwidth usage
    RX_BYTES=$(cat /proc/net/dev | grep "$INTERFACE" | awk '{print $2}')
    sleep 1
    RX_BYTES_NEW=$(cat /proc/net/dev | grep "$INTERFACE" | awk '{print $2}')
    BANDWIDTH=$((RX_BYTES_NEW - RX_BYTES))

    if [[ $BANDWIDTH -gt 10000000 ]]; then  # 10MB/s
        echo "WARNING: High bandwidth usage detected: $BANDWIDTH bytes/sec"
        echo "High bandwidth usage detected on $(hostname)" | \
        mail -s "Bandwidth Alert" security@company.com
    fi
}

# Execute analysis
analyze_traffic
detect_ddos
```

### Security Monitoring Dashboard Script
```bash
#!/bin/bash
# security-dashboard.sh

REPORT_FILE="/tmp/security-dashboard-$(date +%Y%m%d-%H%M%S).html"

generate_security_dashboard() {
    cat << 'EOF' > "$REPORT_FILE"
<!DOCTYPE html>
<html>
<head>
    <title>Security Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; margin-bottom: 20px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
        .alert { background: #e74c3c; color: white; padding: 10px; margin: 10px 0; }
        .warning { background: #f39c12; color: white; padding: 10px; margin: 10px 0; }
        .success { background: #27ae60; color: white; padding: 10px; margin: 10px 0; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .metric { display: inline-block; margin: 10px; padding: 15px; background: #ecf0f1; border-radius: 5px; }
    </style>
    <script>
        function refreshPage() {
            location.reload();
        }
        setInterval(refreshPage, 300000); // Refresh every 5 minutes
    </script>
</head>
<body>
    <div class="header">
        <h1>Security Dashboard - $(hostname)</h1>
        <p>Generated: $(date)</p>
        <p>Auto-refresh: Every 5 minutes</p>
    </div>
EOF

    # System Status
    echo '<div class="section">' >> "$REPORT_FILE"
    echo '<h2>System Status</h2>' >> "$REPORT_FILE"

    UPTIME=$(uptime | awk '{print $3, $4}' | sed 's/,//')
    LOAD=$(cat /proc/loadavg | awk '{print $1, $2, $3}')

    echo "<div class='metric'><strong>Uptime:</strong> $UPTIME</div>" >> "$REPORT_FILE"
    echo "<div class='metric'><strong>Load Average:</strong> $LOAD</div>" >> "$REPORT_FILE"
    echo '</div>' >> "$REPORT_FILE"

    # Security Alerts
    echo '<div class="section">' >> "$REPORT_FILE"
    echo '<h2>Security Alerts</h2>' >> "$REPORT_FILE"

    # Check for active fail2ban bans
    BANNED_COUNT=$(fail2ban-client status 2>/dev/null | grep -o "Currently banned:.*" | awk '{print $3}' || echo "0")
    if [[ $BANNED_COUNT -gt 0 ]]; then
        echo "<div class='alert'>$BANNED_COUNT IPs currently banned by Fail2ban</div>" >> "$REPORT_FILE"
    else
        echo "<div class='success'>No active Fail2ban bans</div>" >> "$REPORT_FILE"
    fi

    # Check for failed login attempts
    FAILED_LOGINS=$(grep "authentication failure" /var/log/auth.log 2>/dev/null | grep "$(date +%b\ %d)" | wc -l || echo "0")
    if [[ $FAILED_LOGINS -gt 10 ]]; then
        echo "<div class='warning'>$FAILED_LOGINS failed login attempts today</div>" >> "$REPORT_FILE"
    fi

    echo '</div>' >> "$REPORT_FILE"

    # Network Status
    echo '<div class="section">' >> "$REPORT_FILE"
    echo '<h2>Network Status</h2>' >> "$REPORT_FILE"
    echo '<table>' >> "$REPORT_FILE"
    echo '<tr><th>Service</th><th>Port</th><th>Status</th></tr>' >> "$REPORT_FILE"

    # Check common services
    services=("22:SSH" "80:HTTP" "443:HTTPS" "2222:SSH-Alt")
    for service in "${services[@]}"; do
        port=$(echo "$service" | cut -d: -f1)
        name=$(echo "$service" | cut -d: -f2)

        if ss -tuln | grep -q ":$port "; then
            status="<span style='color: green;'>Listening</span>"
        else
            status="<span style='color: red;'>Not Listening</span>"
        fi

        echo "<tr><td>$name</td><td>$port</td><td>$status</td></tr>" >> "$REPORT_FILE"
    done

    echo '</table>' >> "$REPORT_FILE"
    echo '</div>' >> "$REPORT_FILE"

    echo '</body></html>' >> "$REPORT_FILE"
}

# Generate dashboard
generate_security_dashboard
echo "Security dashboard generated: $REPORT_FILE"

# Option to serve with simple HTTP server
if command -v python3 &>/dev/null; then
    echo "To view dashboard, run: python3 -m http.server 8080"
    echo "Then open: http://localhost:8080/$(basename "$REPORT_FILE")"
fi
```

## Network Security Best Practices

### Automated Security Hardening Script
```bash
#!/bin/bash
# network-security-hardening.sh

echo "=== Network Security Hardening ==="

# Disable unused network protocols
cat << 'EOF' > /etc/modprobe.d/network-security.conf
# Disable unused network protocols
install dccp /bin/true
install sctp /bin/true
install rds /bin/true
install tipc /bin/true
install atm /bin/true
install cramfs /bin/true
install freevxfs /bin/true
install jffs2 /bin/true
install hfs /bin/true
install hfsplus /bin/true
install squashfs /bin/true
install udf /bin/true
EOF

# Network kernel parameters
cat << 'EOF' > /etc/sysctl.d/99-network-security.conf
# Network security parameters
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.tcp_syncookies = 1
net.ipv6.conf.all.accept_ra = 0
net.ipv6.conf.default.accept_ra = 0
EOF

sysctl --system

# Disable IPv6 if not needed
if [[ "$1" == "--disable-ipv6" ]]; then
    echo "net.ipv6.conf.all.disable_ipv6 = 1" >> /etc/sysctl.d/99-network-security.conf
    echo "net.ipv6.conf.default.disable_ipv6 = 1" >> /etc/sysctl.d/99-network-security.conf
    sysctl -p /etc/sysctl.d/99-network-security.conf
fi

# Close unnecessary ports
echo "Checking for unnecessary open ports..."
ss -tuln | grep LISTEN

echo "Network security hardening completed"
```