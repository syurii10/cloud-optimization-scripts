.PHONY: help install test lint format clean docker-build docker-run terraform-init terraform-plan terraform-apply terraform-destroy

help: ## Показати це повідомлення
	@echo "Cloud Optimization Project - Makefile Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Встановити всі залежності
	pip install -r requirements.txt
	npm install
	@echo "✅ Залежності встановлено"

test: ## Запустити всі тести
	pytest tests/ -v --cov=scripts --cov-report=html
	@echo "✅ Тести виконано"

lint: ## Запустити лінтери
	flake8 scripts/ --max-line-length=127
	black --check scripts/
	pylint scripts/ --exit-zero
	@echo "✅ Лінтинг завершено"

format: ## Форматувати код
	black scripts/
	@echo "✅ Код відформатовано"

clean: ## Очистити тимчасові файли
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*.log' -delete
	rm -rf htmlcov/ .coverage .pytest_cache/
	@echo "✅ Тимчасові файли видалено"

docker-build: ## Збудувати Docker образ
	docker build -t cloud-optimization:latest .
	@echo "✅ Docker образ збудовано"

docker-run: ## Запустити Docker контейнер
	docker-compose up -d
	@echo "✅ Docker контейнер запущено на http://localhost:8080"

docker-stop: ## Зупинити Docker контейнер
	docker-compose down
	@echo "✅ Docker контейнер зупинено"

docker-logs: ## Показати логи Docker контейнера
	docker-compose logs -f

terraform-init: ## Ініціалізувати Terraform
	cd terraform && terraform init
	@echo "✅ Terraform ініціалізовано"

terraform-plan: ## Показати Terraform план
	cd terraform && terraform plan
	@echo "✅ Terraform plan готовий"

terraform-apply: ## Застосувати Terraform конфігурацію
	cd terraform && terraform apply -auto-approve
	@echo "✅ Terraform застосовано"

terraform-destroy: ## Знищити Terraform інфраструктуру
	cd terraform && terraform destroy -auto-approve
	@echo "✅ Terraform інфраструктура знищена"

run-server: ## Запустити веб-сервер
	node server.js

run-simulator: ## Запустити симулятор (потрібен TARGET_URL)
	python scripts/request_simulator.py $(TARGET_URL) 100 60

run-metrics: ## Запустити збір метрик
	python scripts/metrics_collector.py 5 90 metrics.json

run-analyzer: ## Запустити аналізатор даних
	python scripts/data_analyzer.py test_results.json metrics.json

run-optimizer: ## Запустити TOPSIS оптимізатор
	python scripts/optimizer.py

full-test: install lint test ## Повне тестування (install + lint + test)
	@echo "✅ Повне тестування завершено"
