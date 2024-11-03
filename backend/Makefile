.PHONY: migrate run-server debug run_migr

migrate:
	@echo "Applying database migrations..."
	@poetry run alembic upgrade head
	@echo "Migrations applied successfully."

run-server:
	@echo "Starting server..."
	@poetry run python3 run.py


debug:
	sed -i '' 's/DB__HOST=postgres/DB__HOST=localhost/' ../.env
	sed -i '' 's/REDIS_ENDPOINT=redis:\/\/redis:6379/REDIS_ENDPOINT=redis:\/\/localhost:6379/' ../.env
	docker-compose -f debug.yml up -d

run_migr:
	@echo "Applying database migrations..."
	@poetry run alembic upgrade head
	@echo "Migrations applied successfully."
	@echo "Starting server..."
	@poetry run python3 run.py