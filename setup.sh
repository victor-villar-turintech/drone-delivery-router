#!/usr/bin/env bash
# ============================================================
# Drone Delivery Router – Local Setup Script (macOS ARM64)
# ============================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ----------------------------------------------------------
# 1. Load .env
# ----------------------------------------------------------
if [ -f .env ]; then
  info "Loading .env file"
  set -a; source .env; set +a
else
  if [ -f .env.example ]; then
    info "No .env found – copying from .env.example"
    cp .env.example .env
    set -a; source .env; set +a
  else
    warn "No .env or .env.example found. Using defaults."
  fi
fi

# ----------------------------------------------------------
# 2. Check / install Homebrew packages (macOS only)
# ----------------------------------------------------------
if [[ "$(uname)" == "Darwin" ]]; then
  if ! command -v brew &>/dev/null; then
    error "Homebrew is not installed. Visit https://brew.sh to install."
  fi

  BREW_DEPS=(postgresql@14 postgis python@3.11 node)
  for pkg in "${BREW_DEPS[@]}"; do
    if brew list "$pkg" &>/dev/null; then
      info "$pkg is already installed"
    else
      info "Installing $pkg via Homebrew..."
      brew install "$pkg"
    fi
  done

  # Ensure PostgreSQL is running
  if ! pg_isready -q 2>/dev/null; then
    info "Starting PostgreSQL service..."
    brew services start postgresql@14 || true
    sleep 2
  fi
else
  info "Not macOS – skipping Homebrew checks. Ensure PostgreSQL, Python 3.11+, and Node.js are available."
fi

# ----------------------------------------------------------
# 3. Python virtual environment
# ----------------------------------------------------------
info "Setting up Python virtual environment..."
PYTHON_BIN=$(command -v python3.11 || command -v python3 || echo "python3")

if [ ! -d backend/venv ]; then
  "$PYTHON_BIN" -m venv backend/venv
fi
source backend/venv/bin/activate
pip install --upgrade pip --quiet
pip install -r backend/requirements.txt --quiet
info "Python dependencies installed."

# ----------------------------------------------------------
# 4. Database initialization
# ----------------------------------------------------------
DB_NAME="${PGDATABASE:-drone_delivery}"
DB_USER="${PGUSER:-drone_user}"
DB_PASS="${PGPASSWORD:-drone_pass}"

if command -v psql &>/dev/null; then
  info "Checking PostgreSQL database..."

  # Create role if missing (ignore error if exists)
  psql -U postgres -tc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" 2>/dev/null | grep -q 1 || \
    psql -U postgres -c "CREATE ROLE $DB_USER WITH LOGIN PASSWORD '$DB_PASS';" 2>/dev/null || \
    warn "Could not create role $DB_USER – it may already exist or you may need to run as postgres superuser."

  # Create database if missing
  psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null | grep -q 1 || \
    psql -U postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || \
    warn "Could not create database $DB_NAME – it may already exist."

  # Grant privileges
  psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || true

  # Run schema and seed
  info "Applying schema..."
  PGPASSWORD="$DB_PASS" psql -U "$DB_USER" -d "$DB_NAME" -f backend/sql/001_schema.sql 2>/dev/null || \
    warn "Schema application had warnings (tables may already exist)."

  info "Seeding data..."
  PGPASSWORD="$DB_PASS" psql -U "$DB_USER" -d "$DB_NAME" -f backend/sql/002_seed.sql 2>/dev/null || \
    warn "Seed script had warnings (data may already exist)."
else
  warn "psql not found – skipping database initialization. Run the SQL scripts manually."
fi

# ----------------------------------------------------------
# 5. Frontend dependencies
# ----------------------------------------------------------
info "Installing frontend dependencies..."
cd frontend
npm install --silent 2>/dev/null || npm install
cd "$SCRIPT_DIR"

info ""
info "============================================"
info "  Setup complete!"
info "============================================"
info ""
info "Start the backend:"
info "  cd backend && source venv/bin/activate"
info "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
info ""
info "Start the frontend (in another terminal):"
info "  cd frontend && npm run dev"
info ""
info "Dashboard: http://localhost:5173"
info "API docs:  http://localhost:8000/docs"
