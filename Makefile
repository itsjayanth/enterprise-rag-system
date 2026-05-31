.PHONY: help install dev dev-infra dev-backend dev-worker dev-ml dev-frontend \
        stop clean logs test shell-backend shell-db shell-redis

help:
	@echo "Enterprise RAG System - Commands"
	@echo "make dev-infra      Start postgres and redis"
	@echo "make dev            Start full stack"
	@echo "make stop           Stop all containers"
	@echo "make logs           Tail logs"

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev:
	docker compose up -d

dev-infra:
	docker compose up -d postgres redis

dev-backend:
	docker compose up -d postgres redis backend

dev-worker:
	docker compose up -d postgres redis worker

dev-ml:
	docker compose up -d embedding-service reranker-service

dev-frontend:
	docker compose up -d frontend

stop:
	docker compose down

clean:
	docker compose down -v

logs:
	docker compose logs -f

test:
	docker compose exec backend pytest -q

shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U postgres -d enterprise_rag

shell-redis:
	docker compose exec redis redis-cli

