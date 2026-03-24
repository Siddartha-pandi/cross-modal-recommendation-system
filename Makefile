# Hybrid Cross-Modal Fashion Recommendation System
# Makefile for Windows (requires GNU Make — install via: winget install GnuWin32.Make)

# Help Text for the project
HELP_MSG = 'Fashion Recommendation System — Available Commands'
LINE_MSG = '=================================================='

SHELL = powershell.exe
.SHELLFLAGS = -NoProfile -ExecutionPolicy Bypass -Command

BACKEND_DIR  = backend
FRONTEND_DIR = frontend
VENV         = $(BACKEND_DIR)\venv\Scripts

# ── Setup ────────────────────────────────────────────────────────────────────

.PHONY: setup
setup: install-backend install-frontend
	Write-Host ''
	Write-Host '✅  Setup complete!'
	Write-Host "   Run 'make start-backend'  to start the API server"
	Write-Host "   Run 'make start-frontend' to start the UI"
	Write-Host "   Run 'make start'          to start both"

.PHONY: install-backend
install-backend:
	Write-Host '📦  Installing Python dependencies...'
	cd $(BACKEND_DIR); python -m venv venv; .\venv\Scripts\pip install --upgrade pip; .\venv\Scripts\pip install -r requirements.txt
	Write-Host '✅  Backend dependencies installed'

.PHONY: install-frontend
install-frontend:
	Write-Host '📦  Installing Node dependencies...'
	cd $(FRONTEND_DIR); npm install
	Write-Host '✅  Frontend dependencies installed'

# ── Development Servers ───────────────────────────────────────────────────────

.PHONY: start-backend
start-backend:
	Write-Host '🚀  Starting FastAPI backend on http://localhost:8001 ...'
	cd $(BACKEND_DIR); .\venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

.PHONY: start-frontend
start-frontend:
	Write-Host '🚀  Starting Next.js frontend on http://localhost:3000 ...'
	cd $(FRONTEND_DIR); npm run dev

.PHONY: start
start: dev

.PHONY: dev
dev:
	Write-Host '🚀  Starting backend and frontend in separate terminal windows...'
	$$backendPath = Join-Path (Get-Location) '$(BACKEND_DIR)'; \
	$$frontendPath = Join-Path (Get-Location) '$(FRONTEND_DIR)'; \
	Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$$backendPath'; .\venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001"; \
	Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$$frontendPath'; npm run dev"
	Write-Host '✅  Both servers launched in separate windows'
	Write-Host '   Backend → http://localhost:8001'
	Write-Host '   Frontend → http://localhost:3000'
	Write-Host '   API Docs → http://localhost:8001/docs'

# ── Build ─────────────────────────────────────────────────────────────────────

.PHONY: build-index
build-index:
	Write-Host '🔨  Building FAISS index...'
	cd $(BACKEND_DIR); .\venv\Scripts\python scripts/build_index.py
	Write-Host '✅  FAISS index built'

.PHONY: build-frontend
build-frontend:
	Write-Host '🔨  Building Next.js production bundle...'
	cd $(FRONTEND_DIR); npm run build
	Write-Host '✅  Frontend built'

# ── Health Check ──────────────────────────────────────────────────────────────

.PHONY: health
health:
	Write-Host '🔍  Checking backend health...'
	Invoke-RestMethod -Uri http://localhost:8001/api/v1/health | ConvertTo-Json
	Write-Host ''
	Write-Host '🔍  Checking recommend pipeline health...'
	Invoke-RestMethod -Uri http://localhost:8001/api/v1/recommend/health | ConvertTo-Json

# ── Cleanup ───────────────────────────────────────────────────────────────────

.PHONY: clean
clean:
	Write-Host '🧹  Cleaning cache and build artifacts...'
	if (Test-Path $(FRONTEND_DIR)\.next)  { Remove-Item -Recurse -Force $(FRONTEND_DIR)\.next }
	if (Test-Path $(BACKEND_DIR)\app\__pycache__) { Get-ChildItem $(BACKEND_DIR) -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force }
	Write-Host '✅  Clean complete'

# ── Help ─────────────────────────────────────────────────────────────────────

.PHONY: help
help:
	@Write-Host ''
	@Write-Host $(HELP_MSG)
	@Write-Host $(LINE_MSG)
	@Write-Host '  make setup           Install all dependencies'
	@Write-Host '  make install-backend Install Python dependencies only'
	@Write-Host '  make install-frontend Install Node dependencies only'
	@Write-Host '  make start-backend   Start FastAPI server  (port 8001)'
	@Write-Host '  make start-frontend  Start Next.js server  (port 3000)'
	@Write-Host '  make start           Launch both servers (alias for dev)'
	@Write-Host '  make dev             Launch both in new terminal windows'
	@Write-Host '  make build-index     Build FAISS product index'
	@Write-Host '  make build-frontend  Build Next.js production bundle'
	@Write-Host '  make health          Check backend API health'
	@Write-Host '  make clean           Remove cache and build artifacts'
	@Write-Host ''
