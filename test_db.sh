cat << 'DOCKER' > docker-compose-test.yml
version: '3.8'
services:
  db:
    image: postgres:14
    environment:
      - POSTGRES_PASSWORD=turtle_pass
    ports:
      - "5433:5432"
DOCKER
docker compose -f docker-compose-test.yml up -d
sleep 10
