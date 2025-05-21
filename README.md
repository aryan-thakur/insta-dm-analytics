# Standard flow

1. docker-compose build (or up)
2. docker-compose run --rm app python src/main.py
3. docker-compose down

# Interactive flow

1. docker-compose up -d
2. docker-compose exec app bash
3. docker-compose down
