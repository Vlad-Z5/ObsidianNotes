### Network Types and Internals

```bash
# Bridge network (default) - NAT + iptables rules
docker network create \
  --driver bridge \
  --subnet=172.20.0.0/16 \
  --ip-range=172.20.240.0/20 \
  --gateway=172.20.0.1 \
  --opt com.docker.network.bridge.name=custom0 \
  --opt com.docker.network.driver.mtu=1450 \
  custom-bridge

# Overlay network (multi-host) - VXLAN tunneling
docker network create \
  --driver overlay \
  --subnet=10.0.9.0/24 \
  --attachable \
  --opt encrypted=true \
  multi-host-net

# Macvlan network (direct L2 access)
docker network create \
  --driver macvlan \
  --subnet=192.168.1.0/24 \
  --gateway=192.168.1.1 \
  --opt parent=eth0 \
  macvlan-net

# Host network (shares host networking stack)
docker run --network host nginx # No isolation, best performance

# None network (no networking)
docker run --network none alpine # Complete isolation
```

### Container Communication Deep Dive

```bash
# DNS resolution in custom networks
docker network create app-net
docker run -d --name db --network app-net postgres
docker run -d --name web --network app-net nginx
# web can reach db at: db, db.app-net, container-id

# Network aliases
docker run -d --name db --network app-net --network-alias database postgres
# Now reachable as: db, database

# Multiple networks per container
docker network create frontend
docker network create backend
docker run -d --name app --network frontend nginx
docker network connect backend app
# Container now on both networks

# Port mapping internals (iptables NAT rules)
docker run -p 8080:80 nginx # Host:Container
docker run -p 127.0.0.1:8080:80 nginx # Bind to specific interface
docker run -P nginx # Publish all EXPOSE ports randomly

# Network troubleshooting
docker exec container nslookup service-name # DNS resolution check
docker exec container ss -tulpn # Socket statistics
docker exec container ip route # Routing table
docker exec container iptables -L # Firewall rules (if privileged)
```

### Service Discovery Mechanisms

```bash
# Environment variables (legacy)
docker run --link db:database app  # Creates DB_* environment variables

# DNS (preferred in custom networks)
docker network create app-net
docker run -d --name db --network app-net postgres
docker run -d --name web --network app-net nginx
# Automatic DNS: web can resolve 'db' to container IP

# External service discovery
docker run -d \
  --name consul \
  -p 8500:8500 \
  consul:latest agent -server -bootstrap -ui -client=0.0.0.0
```
