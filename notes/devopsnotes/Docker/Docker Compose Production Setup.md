### Advanced Compose Configuration

```yaml
version: '3.8'

x-common-variables: &common-vars
  NODE_ENV: production
  LOG_LEVEL: info
  TZ: UTC

x-restart-policy: &restart-policy
  restart: unless-stopped

x-logging: &default-logging
  logging:
    driver: json-file
    options:
      max-size: "10m"
      max-file: "3"

services:
  web:
    <<: [*restart-policy, *default-logging]
    build:
      context: .
      dockerfile: Dockerfile.prod
      target: runtime
      args:
        - NODE_VERSION=16
        - BUILD_DATE=${BUILD_DATE}
    image: myapp:${VERSION:-latest}
    ports:
      - "8080:3000"
    environment:
      <<: *common-vars
      DATABASE_URL: postgresql://user:${DB_PASSWORD}@db:5432/myapp
    env_file:
      - .env.prod
    volumes:
      - app-logs:/app/logs
      - /etc/localtime:/etc/localtime:ro
    networks:
      - frontend
      - backend
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.50'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

  db:
    <<: [*restart-policy, *default-logging]
    image: postgres:13-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d:ro
      - postgres_config:/etc/postgresql
    networks:
      - backend
    secrets:
      - db_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d myapp"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    sysctls:
      - net.core.somaxconn=1024
    ulimits:
      nproc: 65535
      nofile:
        soft: 26677
        hard: 46677

  redis:
    <<: [*restart-policy, *default-logging]
    image: redis:6-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf:ro
    networks:
      - backend
    sysctls:
      - net.core.somaxconn=1024
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  nginx:
    <<: [*restart-policy, *default-logging]
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./ssl:/etc/nginx/ssl:ro
      - nginx_cache:/var/cache/nginx
    networks:
      - frontend
    depends_on:
      - web
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/postgres-data
  postgres_config:
  redis_data:
  app-logs:
  nginx_cache:

networks:
  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
  backend:
    driver: bridge
    internal: true # No external access

secrets:
  db_password:
    file: ./secrets/db_password.txt
  
configs:
  nginx_config:
    file: ./nginx/nginx.conf
```

### Compose Commands Advanced

```bash
# Environment-specific deployments
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker-compose --env-file .env.prod up -d

# Service management
docker-compose up -d --build --force-recreate web
docker-compose scale web=3 worker=2
docker-compose restart web
docker-compose stop && docker-compose rm -f

# Debugging and monitoring
docker-compose logs -f --tail=100 web
docker-compose exec web sh
docker-compose top
docker-compose ps --services --filter status=running
docker-compose config # Validate and view config
docker-compose events # Real-time events

# Resource management
docker-compose down -v --remove-orphans
docker-compose pull # Update images
```

