#!/usr/bin/env bash
# Single, repeatable production deploy for bpro-hrms-hcm.
#
# Exists because of a real incident: this repo's VPS checkout sat frozen
# at its original `git clone` for weeks with nobody noticing, because
# every "deploy" was a hand-typed sequence of shell commands and `git
# pull` was silently never actually run. This script replaces that whole
# sequence with one command that's either fully correct or loudly fails -
# no partial, unverified state left behind.
#
# Usage (run from anywhere, on the VPS, as the user that owns the repo):
#   /root/bpro-hrms-hcm/deploy/deploy.sh
#
# One-time setup before the first run: create a .env file at the repo
# root (NOT committed - it's in .gitignore) containing:
#   ODOO_ADMIN_PASSWD=<a real, strong password>
# This is the ONLY place that secret lives now. config/odoo.prod.conf
# keeps a harmless CHANGE-ME placeholder in git - this script overwrites
# it with the real value from .env on every run, so a `git reset --hard`
# can never again silently revert it to the public placeholder.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.shared-caddy.yml"

# Every module this suite ships, minus bpro_demo_data (evaluation-only,
# must never run in production - see its own manifest for why).
MODULES="bpro_approval,bpro_attendance,bpro_base,bpro_employment_type,bpro_ess,bpro_exit,bpro_hcm_dashboard,bpro_hr,bpro_hr_letters,bpro_hrms_portal,bpro_leave,bpro_lms,bpro_overtime,bpro_payroll,bpro_pms,bpro_probation,bpro_recruitment,bpro_shifts,bpro_statutory_filing"

log() { echo "[deploy $(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "Starting deploy in $REPO_DIR"

# --- 1. Get the exact latest code, verifiably -----------------------------
# A plain `git pull` can silently no-op if something upstream is wrong
# (this exact repo did, for weeks). Reset hard to the real remote tip
# instead, so success/failure is unambiguous.
log "Fetching latest code..."
git fetch origin
BEFORE_SHA="$(git rev-parse HEAD)"
git reset --hard origin/main
AFTER_SHA="$(git rev-parse HEAD)"
log "HEAD: $BEFORE_SHA -> $AFTER_SHA"

if [ ! -d "addons/bpro_employment_type" ]; then
    echo "[deploy] FATAL: addons/bpro_employment_type missing after reset - the checkout is still wrong. Aborting." >&2
    exit 1
fi

# --- 2. Re-apply the real secret (never stored in git) ---------------------
if [ ! -f "$REPO_DIR/.env" ]; then
    cat >&2 <<'EOF'
[deploy] FATAL: .env not found at the repo root.
Create it once with:
  echo "ODOO_ADMIN_PASSWD=$(openssl rand -base64 24)" > .env
  chmod 600 .env
Then re-run this script.
EOF
    exit 1
fi

# shellcheck disable=SC1091
source "$REPO_DIR/.env"
if [ -z "${ODOO_ADMIN_PASSWD:-}" ]; then
    echo "[deploy] FATAL: ODOO_ADMIN_PASSWD is empty in .env. Aborting." >&2
    exit 1
fi

log "Re-applying admin_passwd from .env into config/odoo.prod.conf..."
sed -i "s|admin_passwd = .*|admin_passwd = $ODOO_ADMIN_PASSWD|" config/odoo.prod.conf

if grep -q "CHANGE-ME" config/odoo.prod.conf; then
    echo "[deploy] FATAL: config/odoo.prod.conf still contains a CHANGE-ME placeholder after the secret substitution. Aborting rather than going live insecure." >&2
    exit 1
fi

# --- 3. Bring up db + odoo (no caddy - this VPS shares one with another project) ---
log "Starting db + odoo containers..."
$COMPOSE up -d db odoo

log "Waiting for Postgres to be healthy..."
for i in $(seq 1 30); do
    health=$($COMPOSE ps db --format '{{.Health}}' 2>/dev/null || true)
    [ "$health" = "healthy" ] && break
    sleep 2
done

# --- 4. Install anything new, upgrade everything else -----------------------
log "Installing/upgrading all modules: $MODULES"
$COMPOSE run --rm --no-deps odoo \
    odoo -c /etc/odoo/odoo.prod.conf -d bpro_prod \
    -i "$MODULES" -u "$MODULES" \
    --without-demo=all --stop-after-init

log "Restarting the live odoo process..."
$COMPOSE restart odoo
sleep 5

# --- 5. Verify it's actually serving before declaring success ---------------
# Derived from the running container, not a hardcoded name - the
# compose project name (and so the container name) follows whatever
# directory this repo happens to be checked out into.
ODOO_CONTAINER=$($COMPOSE ps -q odoo)
HRMS_IP=$(docker inspect "$ODOO_CONTAINER" --format '{{.NetworkSettings.Networks.deploy_default.IPAddress}}')
STATUS=$(curl -s -o /dev/null -w '%{http_code}' "http://$HRMS_IP:8069/web/login" || echo "000")

if [ "$STATUS" != "200" ]; then
    echo "[deploy] FAILED: /web/login returned HTTP $STATUS after restart. Check: docker compose logs odoo" >&2
    exit 1
fi

log "SUCCESS - deployed $AFTER_SHA, /web/login returned 200."
