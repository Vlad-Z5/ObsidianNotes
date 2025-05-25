### Container Security Hardening

```dockerfile
# Multi-layer security approach
FROM alpine:3.15
RUN apk add --no-cache ca-certificates

# Create non-root user with specific UID/GID
RUN addgroup -g 10001 -S appgroup && \
    adduser -u 10001 -S appuser -G appgroup

# Security-focused file operations
COPY --chown=appuser:appgroup app /app/
RUN chmod 755 /app && \
    chmod -R 644 /app/* && \
    chmod 755 /app/entrypoint.sh

USER 10001:10001
WORKDIR /app

# Health check without curl (reduce attack surface)
HEALTHCHECK --interval=30s --timeout=3s \
  CMD /app/healthcheck.sh || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
```

### Runtime Security Configuration

```bash
# Complete security runtime options
docker run -d \
  --name secure-app \
  --user 10001:10001 \                              # Non-root user
  --read-only \                                     # Read-only root filesystem
  --tmpfs /tmp:rw,noexec,nosuid \                  # Writable temp with restrictions
  --tmpfs /var/run:rw,noexec,nosuid \
  --security-opt=no-new-privileges \                # Prevent privilege escalation
  --cap-drop=ALL \                                  # Drop all capabilities
  --cap-add=NET_BIND_SERVICE \                      # Add only needed capabilities
  --security-opt apparmor:docker-default \          # AppArmor profile
  --security-opt seccomp:default.json \             # Seccomp profile
  --pids-limit 100 \                               # Limit process count
  --memory=256m --memory-swap=256m \               # Memory limits
  --cpus="0.5" \                                   # CPU limits
  --ulimit nofile=1024:2048 \                     # File descriptor limits
  --ulimit nproc=50:100 \                         # Process limits
  --restart=on-failure:5 \                        # Restart policy
  --health-cmd="curl -f http://localhost:8080/health" \
  --health-interval=30s \
  --health-timeout=3s \
  --health-retries=3 \
  myapp:latest

# AppArmor profile example
# /etc/apparmor.d/docker-myapp
#include <tunables/global>
profile docker-myapp flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  network,
  capability,
  file,
  umount,
  deny @{PROC}/* w,
  deny /sys/[^f]** wklx,
  deny /sys/f[^s]** wklx,
}

# Seccomp profile (limit system calls)
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": ["accept", "bind", "connect", "listen", "socket"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

### Image Security Scanning

```bash
# Docker Scout (built-in)
docker scout quickview
docker scout cves myapp:latest
docker scout recommendations myapp:latest

# Trivy scanner
trivy image nginx:latest
trivy image --severity HIGH,CRITICAL myapp:latest
trivy fs .  # Scan filesystem

# Snyk scanner
snyk container test nginx:latest
snyk container monitor nginx:latest

# Clair scanner
clair-scanner --ip $(ip route | awk '/docker0/ { print $NF }') myapp:latest

# Custom security scanning in CI/CD
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image myapp:latest
```

### Secrets Management

```bash
# Docker secrets (Swarm mode)
echo "mysecretpassword" | docker secret create db_password -
docker service create \
  --name web \
  --secret db_password \
  --mount type=bind,source=/run/secrets/db_password,target=/app/secret \
  myapp:latest

# External secrets (HashiCorp Vault)
docker run -d \
  --name vault \
  --cap-add=IPC_LOCK \
  -e 'VAULT_DEV_ROOT_TOKEN_ID=myroot' \
  -e 'VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200' \
  vault:latest

# Init containers for secret injection
docker run --rm \
  -v secret-volume:/secrets \
  vault:latest \
  sh -c 'vault kv get -field=password secret/db > /secrets/db_password'

# Runtime secret injection
docker run -d \
  --name app \
  -e DB_PASSWORD_FILE=/run/secrets/db_password \
  -v secret-volume:/run/secrets:ro \
  myapp:latest
```
