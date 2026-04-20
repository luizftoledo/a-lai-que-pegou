#!/bin/bash
# Gera edição semanal da newsletter.
# Executa toda segunda 07h (via launchd) OU no próximo boot se Mac estava off.
# Guard por semana ISO evita execução duplicada.

set -euo pipefail

REPO="/Users/luizfernandotoledo/a-lai-que-pegou"
LOGDIR="$REPO/logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/$(date +%Y-%m-%d_%H%M).log"
exec >> "$LOG" 2>&1

echo "========================================"
echo "START $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================"

GUARD="$REPO/.last-run-week"
WEEK=$(date +%Y-W%V)  # ex: 2026-W17

# Guard: só roda 1x por semana
if [[ -f "$GUARD" && "$(cat "$GUARD")" == "$WEEK" ]]; then
  echo "[guard] já rodou esta semana ($WEEK) — saindo sem fazer nada."
  exit 0
fi

# PATH — launchd não herda user PATH
export PATH="/Users/luizfernandotoledo/.nvm/versions/node/v22.22.0/bin:/Users/luizfernandotoledo/.pyenv/shims:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

cd "$REPO"

# 1. Atualizar repo
echo "[1/5] git pull"
git pull --rebase origin main || { echo "git pull falhou"; exit 1; }

# 2. Coletar pedidos via Playwright
echo "[2/5] scraping buscalai"
python3 scripts/coletar_buscalai.py 90 40 || { echo "scraper falhou"; exit 1; }
mkdir -p docs/data
cp /tmp/pedidos_detalhados.json docs/data/pedidos.json
NUM_PEDIDOS=$(python3 -c "import json; print(len(json.load(open('docs/data/pedidos.json'))))")
echo "[2/5] coletados: $NUM_PEDIDOS pedidos"

# 3. Invocar Claude CLI pra gerar a edição
echo "[3/5] gerando edição com claude"
claude -p "$(cat "$REPO/scripts/prompt-edicao.md")" \
  --add-dir "$REPO" \
  --dangerously-skip-permissions || {
    echo "claude cli falhou"; exit 1
  }

# 4. Commit + push
echo "[4/5] commit + push"
git add docs/
if git diff --cached --quiet; then
  echo "nada pra commitar — provável falha no claude"
  exit 1
fi
git commit -m "edição semanal automática $(date +%Y-%m-%d)"
git pull --rebase origin main || true
git push origin main

# 5. Marcar semana como executada
echo "$WEEK" > "$GUARD"
git add "$GUARD"
git commit -m "guard: week $WEEK done" --quiet || true
git push origin main || true

echo "[5/5] DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)"
