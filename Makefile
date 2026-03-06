.PHONY: help setup install build-index run-backend run-frontend docker-up docker-down docker-rebuild clean test lint test-single test-all test-report

# Default target
help:
	@echo "Cross-Modal Recommendation System - Makefile Commands"
	@echo "======================================================"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make setup          - Install deps + build index"
	@echo "  make install        - Install dependencies only"
	@echo "  make build-index    - Build FAISS index from products"
	@echo ""
	@echo "Development Commands:"
	@echo "  make run-backend    - Run backend server (localhost:8000)"
	@echo "  make run-frontend   - Run frontend dev server (localhost:3000)"
	@echo ""
	@echo "Testing Commands (Hybrid Search):"
	@echo "  make test-single    - Test single example (TC-H01: Red Dress)"
	@echo "  make test-h02       - Test TC-H02 (Blue Denim Jacket)"
	@echo "  make test-all       - Run all 20 test cases (100% pass rate)"
	@echo "  make test-batch-1   - Run TC-H01 to TC-H05"
	@echo "  make test-batch-2   - Run TC-H06 to TC-H10"
	@echo "  make test-batch-3   - Run TC-H11 to TC-H15"
	@echo "  make test-batch-4   - Run TC-H16 to TC-H20"
	@echo "  make test-case CASE=TC-H03 - Run specific test"
	@echo "  make test-range START=TC-H01 END=TC-H05 - Run range"
	@echo "  make test-report    - Generate test report & insights"
	@echo "  make test           - Run pytest suite"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-up      - Start all services with Docker"
	@echo "  make docker-down    - Stop all Docker services"
	@echo "  make docker-rebuild - Rebuild and restart Docker services"
	@echo "  make docker-logs    - View Docker logs"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean          - Clean generated files"
	@echo "  make lint           - Run linters"
	@echo ""

# First-time setup (local dev)
setup: install build-index
	@echo "Local dev setup complete."

# Install dependencies
install:
	@echo "Installing backend dependencies..."
	@cd backend && python -m venv venv
	@cd backend && .\venv\Scripts\python.exe -m pip install --upgrade pip
	@cd backend && .\venv\Scripts\python.exe -m pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install

# Build FAISS index
build-index:
	@echo "Building FAISS index..."
	@cd backend && .\venv\Scripts\python.exe scripts\build_fashion_index.py

# Run backend server
run-backend:
	@echo "Starting backend server on http://localhost:8000"
	@cd backend && .\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run frontend dev server
run-frontend:
	@echo "Starting frontend dev server on http://localhost:3000"
	@cd frontend && npm run dev

# Docker commands
docker-up:
	@echo "Starting Docker unified service..."
	@docker compose up -d --build

docker-down:
	@echo "Stopping Docker services..."
	@docker compose down

docker-rebuild:
	@echo "Rebuilding Docker unified service..."
	@docker compose down
	@docker compose up -d --build

docker-logs:
	@echo "Viewing Docker logs..."
	@docker compose logs -f

# Run single test example - TC-H01
test-single:
	@echo "\n========================================"
	@echo "Testing Single Example (TC-H01)"
	@echo "========================================"
	@python test_search_example.py

# Run TC-H02 test case
test-h02:
	@echo "\n========================================"
	@echo "Testing TC-H02 (Blue Denim Jacket)"
	@echo "========================================"
	@python test_tc_h02.py

# Run all test cases
test-all:
	@echo "\n========================================"
	@echo "Running All 20 Test Cases"
	@echo "========================================"
	@python run_all_tests.py --save-results

# Run specific test case
test-case:
	@echo "Usage: make test-case CASE=TC-H03"
	@python run_all_tests.py --test-ids $(CASE)

# Run range of test cases
test-range:
	@echo "Usage: make test-range START=TC-H01 END=TC-H05"
	@python run_all_tests.py --range $(START):$(END)

# Run first 5 tests
test-batch-1:
	@echo "\n========================================"
	@echo "Running Batch 1 (TC-H01 to TC-H05)"
	@echo "========================================"
	@python run_all_tests.py --range TC-H01:TC-H05 --save-results

# Run tests 6-10
test-batch-2:
	@echo "\n========================================"
	@echo "Running Batch 2 (TC-H06 to TC-H10)"
	@echo "========================================"
	@python run_all_tests.py --range TC-H06:TC-H10 --save-results

# Run tests 11-15
test-batch-3:
	@echo "\n========================================"
	@echo "Running Batch 3 (TC-H11 to TC-H15)"
	@echo "========================================"
	@python run_all_tests.py --range TC-H11:TC-H15 --save-results

# Run tests 16-20
test-batch-4:
	@echo "\n========================================"
	@echo "Running Batch 4 (TC-H16 to TC-H20)"
	@echo "========================================"
	@python run_all_tests.py --range TC-H16:TC-H20 --save-results

# Generate test report
test-report:
	@echo "\n========================================"
	@echo "Generating Test Report"
	@echo "========================================"
	@python generate_workflow_report.py

# Run pytest suite
test:
	@echo "Running pytest suite..."
	@cd backend && .\venv\Scripts\python.exe -m pytest

# Lint code
lint:
	@echo "Running linters..."
	@cd backend && .\venv\Scripts\python.exe -m flake8 app tests

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	@if exist "backend\venv" rmdir /s /q backend\venv
	@if exist "index" rmdir /s /q index
	@if exist "backend\__pycache__" rmdir /s /q backend\__pycache__
	@if exist "backend\app\__pycache__" rmdir /s /q backend\app\__pycache__
	@if exist "backend\.pytest_cache" rmdir /s /q backend\.pytest_cache
	@if exist "frontend\node_modules" rmdir /s /q frontend\node_modules
	@if exist "frontend\.next" rmdir /s /q frontend\.next
	@echo "Clean complete!"
