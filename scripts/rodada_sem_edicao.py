#!/usr/bin/env python3
"""Registra uma rodada que terminou sem edição.

Uso: python3 scripts/rodada_sem_edicao.py AAAA-MM-DD MOTIVO "nota em uma frase"

MOTIVO: sem_pauta (nenhum pedido chegou a 8 pontos) ou fonte_indisponivel
(API e dados abertos falharam ou a base está desatualizada).

Atualiza docs/status.json, que a página inicial lê, e grava
outbox/AAAA-MM-DD.sem-edicao.json. Não altera edições publicadas.
"""
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOTIVOS = {"sem_pauta": "Nenhum pedido respondido na semana atingiu a pontuação mínima.",
           "fonte_indisponivel": "As bases da CGU não puderam ser lidas nesta rodada."}


def main():
    if len(sys.argv) != 4 or sys.argv[2] not in MOTIVOS:
        sys.exit(__doc__)
    dia, motivo, nota = sys.argv[1], sys.argv[2], sys.argv[3].strip()
    date.fromisoformat(dia)
    status_path = ROOT / "docs" / "status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    status.pop("next_run_approx", None)
    status.update({"last_run": datetime.now(timezone.utc).isoformat(), "last_run_status": motivo,
                   "last_run_date": dia, "last_run_note": nota or MOTIVOS[motivo],
                   "last_run_public_note": MOTIVOS[motivo]})
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "outbox").mkdir(exist_ok=True)
    (ROOT / "outbox" / f"{dia}.sem-edicao.json").write_text(json.dumps(
        {"date": dia, "status": motivo, "published": False, "email_sent": False, "note": nota}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Rodada de {dia} registrada: {motivo}")


if __name__ == "__main__":
    main()
