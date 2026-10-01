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
        attachment = (f'<a class="btn ghost" href="{clean(item["attachment_url"])}">Anexo examinado</a>'
                      if item.get("attachment_url") else "")
        context = (f'<a class="btn ghost" href="{clean(item["context_url"])}">Contexto oficial</a>'
                   if item.get("context_url") else "")
        cards.append(f'''<article class="story{' lead' if index == 0 else ''}">
<div class="eyebrow">{index + 1:02d} · {clean(item.get('topic', 'pedido respondido'))} · resposta em {clean(item['response_date'])}</div>
<h2>{clean(item['headline'])}</h2><p class="summary">{clean(item['summary'])}</p>
<p class="why"><strong>Por que agora</strong>{clean(item['why_now'])}</p>
<p class="pitch"><strong>Pista para apuração</strong>{clean(item['pitch'])}</p>
<div class="links"><a class="btn" href="{clean(item['source_url'])}">Ler pedido e resposta na íntegra →</a>{attachment}{context}<span class="protocol">Protocolo {clean(item['protocol'])}</span></div>
</article>''')
    precedents = []
    for p in issue["precedents"]:
        document = (f'<a class="btn ghost" href="{clean(p["document_url"])}">Parecer original (PDF)</a>'
                    if p.get("document_url") else "")
        precedents.append(f'''<article class="precedent"><div class="eyebrow">Decisão · {clean(p['decision_date'])}</div>
<h3>{clean(p['headline'])}</h3><dl class="facts">
<dt>Antes negado</dt><dd>{clean(p['prior_denial'])}</dd>
<dt>Informação a fornecer</dt><dd>{clean(p['opened_information'])}</dd>
<dt>Situação</dt><dd>{clean(p['access_status'])}</dd>
<dt>Por que importa</dt><dd>{clean(p['public_interest'])}</dd>
<dt>O que ficou decidido</dt><dd>{clean(p['decision'])}</dd>
<dt>Como usar em outro pedido</dt><dd>{clean(p['helps_with'])}</dd></dl>
<div class="links"><a class="btn" href="{clean(p['source_url'])}">Ler a decisão →</a>{document}<span class="protocol">Protocolo {clean(p['protocol'])}</span></div></article>''')
    precedent_section = ('''<section class="section"><div class="kicker">Para o próximo pedido</div><h2>Precedentes que ajudam em outros pedidos</h2><p class="precedents-intro">Decisões em recurso que determinaram acesso a informações de interesse público antes negadas. A situação da entrega aparece em cada caso.</p>''' + ''.join(precedents) + '</section>') if precedents else ''
    page = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{clean(issue['headline'])} · A LAI que pegou</title>
<meta name="description" content="{clean(issue['deck'])}"><meta property="og:title" content="{clean(issue['headline'])}"><meta property="og:image" content="https://luizftoledo.github.io/a-lai-que-pegou/assets/capa-lai.gif"><meta name="theme-color" content="#0d2c27">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;1,9..144,500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/style.css?v=2"></head><body>
<div class="topbar"><div class="container"><a class="logo" href="../index.html"><span class="logo-mark" aria-hidden="true"></span>A LAI que pegou</a><nav class="nav"><a href="../index.html#arquivo">Todas as edições</a></nav></div></div>
<header class="hero issue"><div class="container narrow"><div class="issue-meta"><span class="chip"><span class="dot"></span>Edição de {date_label}</span><span class="chip plain">{len(issue['items'])} pistas{f" · {len(issue['precedents'])} precedente" + ("s" if len(issue['precedents']) != 1 else "") if issue['precedents'] else ""}</span></div>
<h1>{clean(issue['headline'])}</h1><p class="lede">{clean(issue['deck'])}</p>
<figure class="cover"><img src="../assets/capa-lai.gif" width="768" height="336" alt="Ilustração animada em pixel art: um jornalista envia um pedido de acesso à informação pelo notebook; o pedido passa por uma plataforma on-line e chega à Controladoria-Geral da União, onde servidores o recebem."></figure></div></header>
<main class="container narrow">
{''.join(cards)}{precedent_section}
<a class="back" href="../index.html#arquivo">← Todas as edições</a></main>
<footer><div class="container narrow"><span>A LAI que pegou · projeto de <a href="https://luizftoledo.github.io/">Luiz Fernando Toledo</a></span><p class="disclaimer">Curadoria de respostas públicas à Lei de Acesso à Informação. Cada achado aponta para o documento oficial. A seleção indica caminhos de apuração; confirmação adicional com órgãos e pessoas citadas cabe à reportagem.</p></div></footer></body></html>'''
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
