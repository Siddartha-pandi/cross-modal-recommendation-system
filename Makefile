# Hybrid Cross-Modal Fashion Recommendation System
# Makefile for Windows (requires GNU Make — install via: winget install GnuWin32.Make)
#
# Usage:
#   make setup          — Install all dependencies (backend + frontend)
#   make start-backend  — Start FastAPI backend on port 8001
#   make start-frontend — Start Next.js frontend on port 3000
#   make dev            — Start both backend and frontend (separate windows)
#   make install-backend  — Install Python dependencies only
#   make install-frontend — Install Node dependencies only
#   make build-index    — Build FAISS index from product data
#   make help           — Show this help

SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -Command

BACKEND_DIR  := backend
FRONTEND_DIR := frontend
VENV         := $(BACKEND_DIR)\venv\Scripts

# ── Setup ────────────────────────────────────────────────────────────────────

.PHONY: setup
setup: install-backend install-frontend
	@echo ""
	@echo "✅  Setup complete!"
	@echo "   Run 'make start-backend'  to start the API server"
	@echo "   Run 'make start-frontend' to start the UI"
	@echo "   Run 'make dev'            to start both"

.PHONY: install-backend
install-backend:
	@echo "📦  Installing Python dependencies..."
	cd $(BACKEND_DIR); python -m venv venv; .\venv\Scripts\pip install --upgrade pip; .\venv\Scripts\pip install -r requirements.txt
	@echo "✅  Backend dependencies installed"

.PHONY: install-frontend
install-frontend:
	@echo "📦  Installing Node dependencies..."
	cd $(FRONTEND_DIR); npm install
	@echo "✅  Frontend dependencies installed"

# ── Development Servers ───────────────────────────────────────────────────────

.PHONY: start-backend
start-backend:
	@echo "🚀  Starting FastAPI backend on http://localhost:8001 ..."
	cd $(BACKEND_DIR); .\venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

.PHONY: start-frontend
start-frontend:
	@echo "🚀  Starting Next.js frontend on http://localhost:3000 ..."
	cd $(FRONTEND_DIR); npm run dev

.PHONY: dev
dev:
	@echo "🚀  Starting backend and frontend in separate terminal windows..."
	Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd "$(CURDIR)\$(BACKEND_DIR)"; .\venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001'
	Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd "$(CURDIR)\$(FRONTEND_DIR)"; npm run dev'
	@echo "✅  Both servers launched in separate windows"
	@echo "   Backend → http://localhost:8001"
	@echo "   Frontend → http://localhost:3000"
	@echo "   API Docs → http://localhost:8001/docs"

# ── Build ─────────────────────────────────────────────────────────────────────

.PHONY: build-index
build-index:
	@echo "🔨  Building FAISS index..."
	cd $(BACKEND_DIR); .\venv\Scripts\python scripts/build_index.py
	@echo "✅  FAISS index built"

.PHONY: build-frontend
build-frontend:
	@echo "🔨  Building Next.js production bundle..."
	cd $(FRONTEND_DIR); npm run build
	@echo "✅  Frontend built"

# ── Health Check ──────────────────────────────────────────────────────────────

.PHONY: health
health:
	@echo "🔍  Checking backend health..."
	Invoke-RestMethod -Uri http://localhost:8001/api/v1/health | ConvertTo-Json
	@echo ""
	@echo "🔍  Checking recommend pipeline health..."
	Invoke-RestMethod -Uri http://localhost:8001/api/v1/recommend/health | ConvertTo-Json

# ── Cleanup ───────────────────────────────────────────────────────────────────

.PHONY: clean
clean:
	@echo "🧹  Cleaning cache and build artifacts..."
	if (Test-Path $(FRONTEND_DIR)\.next)  { Remove-Item -Recurse -Force $(FRONTEND_DIR)\.next }
	if (Test-Path $(BACKEND_DIR)\app\__pycache__) { Get-ChildItem $(BACKEND_DIR) -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force }
	@echo "✅  Clean complete"

# ── Help ─────────────────────────────────────────────────────────────────────

.PHONY: help
help:
	@echo ""
	@echo "Fashion Recommendation System — Available Commands"
	@echo "=================================================="
	@echo "  make setup           Install all dependencies"
	@echo "  make install-backend Install Python dependencies only"
	@echo "  make install-frontend Install Node dependencies only"
	@echo "  make start-backend   Start FastAPI server  (port 8001)"
	@echo "  make start-frontend  Start Next.js server  (port 3000)"
	@echo "  make dev             Launch both in new terminal windows"
	@echo "  make build-index     Build FAISS product index"
	@echo "  make build-frontend  Build Next.js production bundle"
	@echo "  make health          Check backend API health"
	@echo "  make clean           Remove cache and build artifacts"
	@echo ""
