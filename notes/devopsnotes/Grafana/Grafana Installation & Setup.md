### Docker Installation

```bash
# Run Grafana with persistent storage
docker run -d --name grafana \
  -p 3000:3000 \
  -v grafana-storage:/var/lib/grafana \
  -e "GF_SECURITY_ADMIN_PASSWORD=admin123" \
  grafana/grafana-oss:latest

# With custom configuration
docker run -d --name grafana \
  -p 3000:3000 \
  -v /path/to/grafana.ini:/etc/grafana/grafana.ini \
  -v grafana-data:/var/lib/grafana \
  grafana/grafana-oss:latest

# Docker Compose
version: '3.8'
services:
  grafana:
    image: grafana/grafana-oss:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SMTP_ENABLED=true
      - GF_SMTP_HOST=smtp.gmail.com:587
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    restart: unless-stopped
```

### Package Installation

```bash
# Ubuntu/Debian
curl -fsSL https://packages.grafana.com/gpg.key | sudo gpg --dearmor -o /usr/share/keyrings/grafana.gpg
echo "deb [signed-by=/usr/share/keyrings/grafana.gpg] https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update && sudo apt install grafana

# RHEL/CentOS
sudo yum install -y https://dl.grafana.com/oss/release/grafana-10.2.0-1.x86_64.rpm

# Start service
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
sudo systemctl status grafana-server
```

### Basic Configuration

```ini
# /etc/grafana/grafana.ini
[server]
protocol = http
http_addr = 0.0.0.0
http_port = 3000
domain = localhost
root_url = %(protocol)s://%(domain)s:%(http_port)s/
serve_from_sub_path = false

[database]
type = sqlite3
path = grafana.db
host = 127.0.0.1:3306
name = grafana
user = root
password = 

[auth]
disable_login_form = false
disable_signout_menu = false

[auth.anonymous]
enabled = false
org_name = Main Org.
org_role = Viewer

[security]
admin_user = admin
admin_password = admin
secret_key = SW2YcwTIb9zpOOhoPsMm
cookie_secure = false
cookie_samesite = lax

[smtp]
enabled = true
host = localhost:587
user = admin@grafana.localhost
password = password
skip_verify = false
from_address = admin@grafana.localhost
from_name = Grafana

[log]
mode = console file
level = info
```
