#!/usr/bin/env bash
# scripts/dev_workflow.sh
# ─────────────────────────────────────────────────────────────────
# Senior engineering Git workflow:
#   1. Create feature branch
#   2. Run ruff lint + format
#   3. Run pytest with coverage
#   4. If all pass → merge to develop
#   5. Never touch main directly
#
# Usage:
#   chmod +x scripts/dev_workflow.sh
#   ./scripts/dev_workflow.sh feature/add-ppt-report
# ─────────────────────────────────────────────────────────────────

set -euo pipefail   # exit on error, unset var, pipe failure

BRANCH_NAME="${1:-}"
DEVELOP="develop"
COVERAGE_MIN=75

# ── Colors ────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log_step()  { echo -e "\n${CYAN}${BOLD}▶  $1${NC}"; }
log_ok()    { echo -e "${GREEN}✅  $1${NC}"; }
log_fail()  { echo -e "${RED}❌  $1${NC}"; }
log_warn()  { echo -e "${YELLOW}⚠   $1${NC}"; }

# ── Guard: branch name required ───────────────────────────────────
if [[ -z "$BRANCH_NAME" ]]; then
  log_fail "Usage: $0 <branch-name>  (e.g. feature/add-ppt-report)"
  exit 1
fi

if [[ "$BRANCH_NAME" == "main" || "$BRANCH_NAME" == "develop" ]]; then
  log_fail "Never work directly on '$BRANCH_NAME'. Use a feature branch."
  exit 1
fi

# ── Guard: clean working tree ─────────────────────────────────────
if [[ -n "$(git status --porcelain)" ]]; then
  log_warn "Uncommitted changes detected. Commit or stash before proceeding."
  git status --short
  exit 1
fi

# ── Step 1: Create or switch to feature branch ────────────────────
log_step "Step 1/5 — Setting up branch: $BRANCH_NAME"

CURRENT=$(git branch --show-current)

if git show-ref --quiet "refs/heads/$BRANCH_NAME"; then
  log_warn "Branch '$BRANCH_NAME' already exists. Switching to it."
  git checkout "$BRANCH_NAME"
else
  git checkout "$DEVELOP" 2>/dev/null || git checkout -b "$DEVELOP"
  git pull origin "$DEVELOP" 2>/dev/null || true
  git checkout -b "$BRANCH_NAME"
  log_ok "Created branch '$BRANCH_NAME' from '$DEVELOP'"
fi

# ── Step 2: Ruff format ───────────────────────────────────────────
log_step "Step 2/5 — Ruff: auto-format code"

if ! command -v ruff &>/dev/null; then
  log_warn "ruff not found. Installing..."
  pip install "ruff>=0.4.0" -q
fi

ruff format .
log_ok "Code formatted"

# ── Step 3: Ruff lint ─────────────────────────────────────────────
log_step "Step 3/5 — Ruff: lint check"

if ruff check . --fix; then
  log_ok "Lint passed (auto-fixed where possible)"
else
  log_fail "Lint errors found that could not be auto-fixed."
  echo "Run 'ruff check . --fix' and resolve manually."
  exit 1
fi

# ── Step 4: Pytest ────────────────────────────────────────────────
log_step "Step 4/5 — Pytest: run full test suite"

if ! command -v pytest &>/dev/null; then
  log_warn "pytest not found. Installing dev deps..."
  pip install -r requirements-dev.txt -q
fi

if pytest tests/ \
    --cov=. \
    --cov-report=term-missing \
    --cov-fail-under="$COVERAGE_MIN" \
    -v \
    --tb=short; then
  log_ok "All tests passed (coverage ≥ ${COVERAGE_MIN}%)"
else
  log_fail "Tests failed. Fix errors before merging."
  exit 1
fi

# ── Step 5: Merge to develop ──────────────────────────────────────
log_step "Step 5/5 — Merging '$BRANCH_NAME' → '$DEVELOP'"

read -rp "$(echo -e "${YELLOW}Merge to '$DEVELOP'? [y/N]: ${NC}")" CONFIRM
if [[ "${CONFIRM,,}" != "y" ]]; then
  log_warn "Merge skipped. Branch '$BRANCH_NAME' is ready whenever you are."
  exit 0
fi

git add -A
git diff --cached --quiet || git commit -m "chore: auto-format via ruff [ci skip]" 2>/dev/null || true

git checkout "$DEVELOP"
git pull origin "$DEVELOP" 2>/dev/null || true
git merge --no-ff "$BRANCH_NAME" -m "merge: $BRANCH_NAME → $DEVELOP"

log_ok "Merged '$BRANCH_NAME' into '$DEVELOP'"
echo ""
echo -e "${BOLD}Next steps:${NC}"
echo "  git push origin $DEVELOP   → triggers CI/CD pipeline"
echo "  CI: lint → test → deploy staging → (manual) deploy prod"
echo ""
echo -e "${GREEN}${BOLD}Done! 🎉${NC}"
