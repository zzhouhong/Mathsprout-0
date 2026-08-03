#!/bin/bash
set -e

echo "=== 幼儿园数学教育智能体 — 生产部署 ==="

# Check for certs
if [ ! -f "./certs/fullchain.pem" ] || [ ! -f "./certs/privkey.pem" ]; then
    echo "WARNING: SSL certs not found in ./certs/. HTTPS will fail."
    echo "Place your fullchain.pem and privkey.pem in ./certs/ before deploying."
fi

# Build and start
echo "Building Docker images..."
docker compose -f docker-compose.prod.yml build

echo "Starting services..."
docker compose -f docker-compose.prod.yml up -d

# Wait for DB
echo "Waiting for PostgreSQL..."
sleep 5

# Run migrations
echo "Running Alembic migrations..."
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

echo ""
echo "Deployment complete!"
echo "Frontend : https://your-domain.com"
echo "API Docs : https://your-domain.com/api/docs"
echo ""
echo "Next steps:"
echo "  1. Update SECRET_KEY in docker-compose.prod.yml"
echo "  2. Update DB password in docker-compose.prod.yml"
echo "  3. Update your-domain.com in nginx.conf"
echo "  4. Place SSL certs in ./certs/"
