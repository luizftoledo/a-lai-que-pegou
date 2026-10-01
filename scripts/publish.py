#!/usr/bin/env python3
"""Validate a reported issue and render the website and email text.

Usage: python3 scripts/publish.py issues/YYYY-MM-DD.json
The issue is written by an editor after reading the linked official records.
This program never invents or selects stories.
"""
import html
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def clean(value):
    return html.escape(str(value).strip(), quote=True)


def official(url, kinds):
    host = (urlparse(url).hostname or "").lower()
    return urlparse(url).scheme == "https" and any(host == domain or host.endswith("." + domain) for domain in kinds)


def validate(issue):
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", issue["date"])
    date.fromisoformat(issue["date"])
    assert issue["headline"].strip() and issue["deck"].strip()
    assert 1 <= len(issue["items"]) <= 6, "Publish only verified findings; aim for six."
    assert issue["headline"] == issue["items"][0]["headline"], "The edition title must be the strongest reported finding."
    assert isinstance(issue.get("precedents"), list), "Precedents must be a list, even when no decision qualifies."
    seen = set()
    for item in issue["items"]:
        for field in ("headline", "summary", "why_now", "pitch", "source_url", "protocol", "response_date", "evidence", "attachment_review"):
            assert str(item.get(field, "")).strip(), f"Missing {field} in request"
        assert official(item["source_url"], ("cgu.gov.br", "gov.br"))
        assert item["source_url"] not in seen, "Duplicate request"
        seen.add(item["source_url"])
        date.fromisoformat(item["response_date"])
        assert len(item["evidence"]) >= 20, "Record the exact supporting passage or data."
        if item.get("attachment_url"):
            assert official(item["attachment_url"], ("cgu.gov.br", "gov.br"))
        if item.get("context_url"):
            assert official(item["context_url"], ("gov.br",))
    for p in issue["precedents"]:
        for field in ("headline", "decision", "prior_denial", "opened_information", "public_interest", "access_status", "helps_with", "source_url", "protocol", "decision_date", "evidence"):
            assert str(p.get(field, "")).strip(), f"Missing {field} in precedent"
        assert p["access_status"] in ("entrega determinada", "entrega confirmada"), "Distinguish an access order from confirmed disclosure."
        assert official(p["source_url"], ("cgu.gov.br", "gov.br"))
        if p.get("document_url"):
            assert official(p["document_url"], ("cgu.gov.br", "gov.br"))
        date.fromisoformat(p["decision_date"])


def render(issue):
    date_label = date.fromisoformat(issue["date"]).strftime("%d/%m/%Y")
    cards = []
    for index, item in enumerate(issue["items"]):
        attachment = (f'<p class="source"><a href="{clean(item["attachment_url"])}">Ver anexo examinado →</a></p>'
                      if item.get("attachment_url") else "")
        context = (f'<p class="source"><a href="{clean(item["context_url"])}">Ver contexto oficial →</a></p>'
                   if item.get("context_url") else "")
        cards.append(f'''<article class="story{' lead' if index == 0 else ''}">
<div class="eyebrow">{index + 1:02d} · {clean(item.get('topic', 'pedido respondido'))} · resposta em {clean(item['response_date'])}</div>
<h2>{clean(item['headline'])}</h2><p class="summary">{clean(item['summary'])}</p>
<p><strong>Por que agora:</strong> {clean(item['why_now'])}</p>
<p><strong>Pista para apuração:</strong> {clean(item['pitch'])}</p>
<p class="source"><a href="{clean(item['source_url'])}">Ler pedido e resposta na íntegra →</a> <span>Protocolo {clean(item['protocol'])}</span></p>{attachment}{context}
</article>''')
    precedents = []
    for p in issue["precedents"]:
        document = (f'<p class="source"><a href="{clean(p["document_url"])}">Ler parecer original (PDF) →</a></p>'
                    if p.get("document_url") else "")
        precedents.append(f'''<article class="precedent"><div class="eyebrow">DECISÃO · {clean(p['decision_date'])}</div>
<h3>{clean(p['headline'])}</h3><p><strong>Antes negado:</strong> {clean(p['prior_denial'])}</p>
<p><strong>Informação a fornecer:</strong> {clean(p['opened_information'])}</p><p><strong>Situação:</strong> {clean(p['access_status'])}</p>
<p><strong>Por que importa:</strong> {clean(p['public_interest'])}</p><p><strong>O que ficou decidido:</strong> {clean(p['decision'])}</p>
<p><strong>Como usar em outro pedido:</strong> {clean(p['helps_with'])}</p>
<p class="source"><a href="{clean(p['source_url'])}">Ler a decisão →</a> <span>Protocolo {clean(p['protocol'])}</span></p>{document}</article>''')
    precedent_section = ('''<section><h2>Precedentes que ajudam em outros pedidos</h2><p>Decisões em recurso que determinaram acesso a informações de interesse público antes negadas. A situação da entrega aparece em cada caso.</p>''' + ''.join(precedents) + '</section>') if precedents else ''
    page = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{clean(issue['headline'])} · A LAI que pegou</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f8faf8;color:#18332e;font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
.wrap{{max-width:760px;margin:auto;padding:34px 22px 70px}}header{{border-top:5px solid #237b70;padding-top:18px;border-bottom:1px solid #c9d8d2;padding-bottom:24px}}
.brand{{font:700 32px/1.1 Georgia,serif;letter-spacing:-1px}}.eyebrow{{color:#356f68;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}}
h1,h2,h3{{font-family:Georgia,serif;line-height:1.16;letter-spacing:-.025em}}h1{{font-size:clamp(32px,6vw,48px);margin:20px 0 12px}}h2{{font-size:28px;margin:9px 0}}h3{{font-size:23px;margin:8px 0}}
.deck{{font-size:20px;color:#34554f}}.story{{padding:27px 0;border-bottom:1px solid #c9d8d2}}.lead{{padding:35px 25px;margin:28px -25px 0;background:#e8f3ee;border-left:4px solid #237b70;border-bottom:0}}
.summary{{font-size:18px;font-weight:550}}.source{{font-size:14px}}a{{color:#176d62;text-decoration:underline;text-underline-offset:3px}}.source span{{color:#658079;margin-left:8px}}.muted{{color:#658079;font-size:14px}}
.cover{{margin:24px 0 10px;background:#f3f1e9;border:1px solid #d5d3ca;overflow:hidden}}.cover img{{display:block;width:100%;height:auto}}.cover figcaption{{padding:4px 12px 9px;color:#6a6c68;font:11px/1.4 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;text-align:right;letter-spacing:.04em}}
section{{margin-top:42px}}section>h2{{border-top:3px solid #237b70;padding-top:15px}}.precedent{{padding:20px 0;border-bottom:1px solid #c9d8d2}}
footer{{border-top:1px solid #c9d8d2;margin-top:50px;padding-top:18px;color:#58736c;font-size:13px}}@media(max-width:600px){{.lead{{margin:24px 0 0;padding:22px}}.source span{{display:block;margin:4px 0}}}}
</style></head><body><div class="wrap"><header><div class="brand">A LAI que pegou</div><div class="eyebrow">Edição de {date_label} · pistas para jornalistas</div></header>
<figure class="cover"><img src="../assets/capa-lai.svg" width="960" height="360" alt="Ilustração animada: jornalista envia um pedido pelo e-SIC; servidores de um órgão público consultam documentos e preparam a resposta."><figcaption>DO PEDIDO À RESPOSTA · ILUSTRAÇÃO ANIMADA</figcaption></figure>
<main><h1>{clean(issue['headline'])}</h1><p class="deck">{clean(issue['deck'])}</p>
{''.join(cards)}{precedent_section}</main>
<footer>Curadoria de respostas públicas à Lei de Acesso à Informação. Cada achado aponta para o documento oficial. A seleção indica caminhos de apuração; confirmação adicional com órgãos e pessoas citadas cabe à reportagem. <a href="../index.html">Todas as edições</a>.</footer></div></body></html>'''
    lines = ["A LAI que pegou", f"Edição de {date_label}", "", issue["headline"], issue["deck"],
             "", "Edição na web: https://luizftoledo.github.io/a-lai-que-pegou/edicoes/" + issue["date"] + ".html", ""]
    for item in issue["items"]:
        lines += [item["headline"], item["summary"], "Por que agora: " + item["why_now"], "Pista para apuração: " + item["pitch"], "Íntegra: " + item["source_url"]]
        if item.get("context_url"):
            lines.append("Contexto oficial: " + item["context_url"])
        lines.append("")
    if issue["precedents"]:
        lines += ["PRECEDENTES QUE AJUDAM EM OUTROS PEDIDOS", ""]
        for p in issue["precedents"]:
            lines += [p["headline"], "Antes negado: " + p["prior_denial"], "Informação a fornecer: " + p["opened_information"], "Situação: " + p["access_status"], "Interesse público: " + p["public_interest"], "Decisão: " + p["decision"], "Como usar: " + p["helps_with"], "Íntegra: " + p["source_url"]]
            if p.get("document_url"):
                lines += ["Parecer (PDF): " + p["document_url"]]
            lines += [""]
    return page, "\n".join(lines)


def main():
    issue_path = Path(sys.argv[1]).resolve()
    assert issue_path.parent == ROOT / "issues", "Issue must live in issues/"
    issue = json.loads(issue_path.read_text(encoding="utf-8"))
    assert issue_path.stem == issue["date"]
    validate(issue)
    page, email = render(issue)
    (DOCS / "edicoes").mkdir(parents=True, exist_ok=True)
    (DOCS / "edicoes" / f"{issue['date']}.html").write_text(page, encoding="utf-8")
    (ROOT / "outbox").mkdir(exist_ok=True)
    (ROOT / "outbox" / f"{issue['date']}.txt").write_text(email, encoding="utf-8")
    status_path = DOCS / "status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    entries = [x for x in status.get("edicoes", []) if x.get("data") != issue["date"]]
    entries.append({"numero": max([x.get("numero", 0) for x in entries] + [0]) + 1,
                    "data": issue["date"], "file": f"edicoes/{issue['date']}.html",
                    "titulo": issue["headline"], "em_destaque": issue["deck"],
                    "e_mais": len(issue["items"]) - 1, "precedentes": len(issue["precedents"])})
    status.update({"last_run": datetime.now(timezone.utc).isoformat(), "last_run_status": "success",
                   "last_run_note": f"{len(issue['items'])} pedidos e {len(issue['precedents'])} precedentes verificados",
                   "edicoes": entries})
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Published {issue['date']} with {len(issue['items'])} requests and {len(issue['precedents'])} precedents")


if __name__ == "__main__":
    main()
