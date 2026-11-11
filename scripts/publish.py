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


CRITERIOS_DESDE = "2026-11-11"  # edições anteriores não têm o registro de relevância
EIXOS = ("alcance", "efeito", "solidez", "atualidade", "clareza")
SIGLAS_LIVRES = {
    "INSS", "SUS", "CPF", "CNPJ", "FGTS", "IBGE", "EUA", "ONU", "STF", "STJ", "TCU", "CGU", "LAI", "PIB",
    "MEC", "ENEM", "IPTU", "IPVA", "ICMS", "BNDES", "IBAMA", "FAB", "PIX", "CLT", "MEI", "SAMU", "UTI",
    "HIV", "COVID", "PCC", "ONG", "CPI", "PEC", "BPC", "CNH", "IPCA", "USP", "OAB", "ANVISA", "ANATEL",
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE",
    "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}


def published_protocols(current_date):
    seen = {}
    for path in (ROOT / "issues").glob("*.json"):
        if path.stem == current_date:
            continue
        other = json.loads(path.read_text(encoding="utf-8"))
        for block in ("items", "precedents", "tambem_responderam"):
            for x in other.get(block, []):
                seen[x.get("protocol", "")] = path.stem
    return seen


def check_headline(text, where, errors):
    if len(text) > 90:
        errors.append(f"{where}: título com {len(text)} caracteres (máximo 90).")
    siglas = [w for w in re.findall(r"\b[A-ZÀ-Ý]{3,}\b", text) if w not in SIGLAS_LIVRES]
    if siglas:
        errors.append(f"{where}: sigla fora do uso corrente no título ({', '.join(siglas)}); escrever por extenso.")
    if len(re.findall(r"\d[\d.,]*", text)) > 2:
        errors.append(f"{where}: mais de dois números no título.")


def check_relevance(item, where, issue_date, first, errors):
    rel = item.get("relevancia")
    if not isinstance(rel, dict):
        errors.append(f"{where}: falta o registro `relevancia` (ver CRITERIOS.md).")
        return 0
    pontos, motivos = rel.get("pontos", {}), rel.get("motivos", {})
    for eixo in EIXOS:
        if pontos.get(eixo) not in (0, 1, 2, 3):
            errors.append(f"{where}: pontos de {eixo} devem ser 0, 1, 2 ou 3.")
        if len(str(motivos.get(eixo, "")).strip()) < 15:
            errors.append(f"{where}: falta o motivo escrito para {eixo}.")
    if any(pontos.get(e) not in (0, 1, 2, 3) for e in EIXOS):
        return 0
    total = sum(pontos[e] for e in EIXOS)
    if total < 8:
        errors.append(f"{where}: {total} pontos. Item exige 8; de 5 a 7 vai para `tambem_responderam`.")
    if first and (pontos["alcance"] < 2 or pontos["clareza"] < 2):
        errors.append(f"{where}: a abertura exige alcance e clareza de pelo menos 2.")
    if rel.get("cobertura") not in ("nao_coberto", "coberto_sem_o_dado"):
        errors.append(f"{where}: `cobertura` deve ser nao_coberto ou coberto_sem_o_dado; assunto bem coberto fica fora.")
    if rel.get("verificado_por") not in ("api", "pagina", "dados_abertos"):
        errors.append(f"{where}: `verificado_por` deve ser api, pagina ou dados_abertos.")
    if item.get("tipo", "resposta") == "negativa" and (pontos["alcance"] < 3 or pontos["efeito"] < 3):
        errors.append(f"{where}: negativa só entra com alcance 3 e efeito 3.")
    if item.get("tipo", "resposta") not in ("resposta", "negativa"):
        errors.append(f"{where}: `tipo` deve ser resposta ou negativa.")
    age = (date.fromisoformat(issue_date) - date.fromisoformat(item["response_date"])).days
    if not 0 <= age <= 21:
        errors.append(f"{where}: resposta de {item['response_date']} está fora da janela de 21 dias da edição.")
    if len(item["evidence"]) < 80:
        errors.append(f"{where}: `evidence` precisa do trecho literal ou dos números exatos (mínimo de 80 caracteres).")
    return total


def validate(issue):
    """Devolve a lista de problemas; vazia quando a edição pode ser publicada."""
    errors = []
    try:
        date.fromisoformat(issue["date"])
    except (KeyError, ValueError):
        return ["`date` deve ser AAAA-MM-DD."]
    strict = issue["date"] >= CRITERIOS_DESDE
    for field in ("headline", "deck"):
        if not str(issue.get(field, "")).strip():
            errors.append(f"Falta `{field}` na edição.")
    items = issue.get("items") or []
    if not 1 <= len(items) <= 6:
        errors.append("A edição precisa de 1 a 6 itens verificados.")
    if not isinstance(issue.get("precedents"), list):
        errors.append("`precedents` deve ser uma lista, mesmo vazia.")
    if errors:
        return errors
    if issue["headline"] != items[0].get("headline"):
        errors.append("O título da edição deve ser igual ao do primeiro item.")
    earlier = published_protocols(issue["date"]) if strict else {}
    seen, totals = set(), []
    for n, item in enumerate(items, 1):
        where = f"Item {n}"
        missing = [f for f in ("headline", "summary", "why_now", "pitch", "source_url", "protocol", "response_date", "evidence", "attachment_review")
                   if not str(item.get(f, "")).strip()]
        if missing:
            errors.append(f"{where}: faltam {', '.join(missing)}.")
            continue
        try:
            date.fromisoformat(item["response_date"])
        except ValueError:
            errors.append(f"{where}: `response_date` deve ser AAAA-MM-DD.")
            continue
        if not official(item["source_url"], ("gov.br",)):
            errors.append(f"{where}: `source_url` deve ser https em domínio gov.br.")
        for field in ("attachment_url", "context_url"):
            if item.get(field) and not official(item[field], ("gov.br",)):
                errors.append(f"{where}: `{field}` deve ser https em domínio gov.br.")
        if item["source_url"] in seen:
            errors.append(f"{where}: pedido repetido na mesma edição.")
        seen.add(item["source_url"])
        if len(item["evidence"]) < 20:
            errors.append(f"{where}: `evidence` vazio ou curto demais.")
        if strict:
            if item["protocol"] in earlier:
                errors.append(f"{where}: protocolo já publicado na edição de {earlier[item['protocol']]}.")
            check_headline(item["headline"], where, errors)
            totals.append(check_relevance(item, where, issue["date"], n == 1, errors))
    if strict and totals and totals[0] < max(totals):
        errors.append("O primeiro item deve ser o de maior pontuação.")
    if strict and totals and totals[0] < 11 and sum(t >= 8 for t in totals) < 2:
        errors.append("Sem item com 11 pontos, a edição só sai com pelo menos dois itens de 8 ou mais.")
    for n, x in enumerate(issue.get("tambem_responderam", []), 1):
        where = f"Também responderam {n}"
        if any(not str(x.get(f, "")).strip() for f in ("headline", "summary", "source_url", "protocol")):
            errors.append(f"{where}: precisa de headline, summary, source_url e protocol.")
            continue
        if not official(x["source_url"], ("gov.br",)):
            errors.append(f"{where}: `source_url` deve ser https em domínio gov.br.")
        if len(x["summary"]) > 300:
            errors.append(f"{where}: resumo de uma linha, até 300 caracteres.")
        if x["protocol"] in earlier:
            errors.append(f"{where}: protocolo já publicado na edição de {earlier[x['protocol']]}.")
    for n, p in enumerate(issue["precedents"], 1):
        where = f"Precedente {n}"
        missing = [f for f in ("headline", "decision", "prior_denial", "opened_information", "public_interest", "access_status", "helps_with", "source_url", "protocol", "decision_date", "evidence")
                   if not str(p.get(f, "")).strip()]
        if missing:
            errors.append(f"{where}: faltam {', '.join(missing)}.")
            continue
        if p["access_status"] not in ("entrega determinada", "entrega confirmada"):
            errors.append(f"{where}: `access_status` deve ser 'entrega determinada' ou 'entrega confirmada'.")
        for field in ("source_url", "document_url"):
            if p.get(field) and not official(p[field], ("gov.br",)):
                errors.append(f"{where}: `{field}` deve ser https em domínio gov.br.")
        try:
            date.fromisoformat(p["decision_date"])
        except ValueError:
            errors.append(f"{where}: `decision_date` deve ser AAAA-MM-DD.")
    return errors


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
    also = issue.get("tambem_responderam", [])
    also_section = ('<section class="section"><div class="kicker">Em uma linha</div><h2>Também responderam</h2><ul class="also">' + ''.join(
        f'<li><a href="{clean(x["source_url"])}">{clean(x["headline"])}</a>. {clean(x["summary"])} <span class="protocol">Protocolo {clean(x["protocol"])}</span></li>'
        for x in also) + '</ul></section>') if also else ''
    n_items = len(issue['items'])
    precedent_section = ('''<section class="section"><div class="kicker">Para o próximo pedido</div><h2>Precedentes que ajudam em outros pedidos</h2><p class="precedents-intro">Decisões em recurso que determinaram acesso a informações de interesse público antes negadas. A situação da entrega aparece em cada caso.</p>''' + ''.join(precedents) + '</section>') if precedents else ''
    page = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{clean(issue['headline'])} · A LAI que pegou</title>
<meta name="description" content="{clean(issue['deck'])}"><meta property="og:title" content="{clean(issue['headline'])}"><meta property="og:image" content="https://luizftoledo.github.io/a-lai-que-pegou/assets/capa-lai.gif"><meta name="theme-color" content="#0d2c27">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;1,9..144,500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/style.css?v=3"></head><body>
<div class="topbar"><div class="container"><a class="logo" href="../index.html"><span class="logo-mark" aria-hidden="true"></span>A LAI que pegou</a><nav class="nav"><a href="../index.html#arquivo">Todas as edições</a></nav></div></div>
<header class="hero issue"><div class="container narrow"><div class="issue-meta"><span class="chip"><span class="dot"></span>Edição de {date_label}</span><span class="chip plain">{n_items} pista{'s' if n_items != 1 else ''}{f" · {len(issue['precedents'])} precedente" + ("s" if len(issue['precedents']) != 1 else "") if issue['precedents'] else ""}</span></div>
<h1>{clean(issue['headline'])}</h1><p class="lede">{clean(issue['deck'])}</p>
<figure class="cover"><img src="../assets/capa-lai.gif?v=4" width="768" height="336" alt="Ilustração animada em pixel art: um jornalista envia pedidos de acesso à informação pela internet à Controladoria-Geral da União; as respostas voltam para ele e viram reportagens na TV, no jornal e no celular."></figure></div></header>
<main class="container narrow">
{''.join(cards)}{also_section}{precedent_section}
<a class="back" href="../index.html#arquivo">← Todas as edições</a></main>
<footer><div class="container narrow"><span>A LAI que pegou · projeto de <a href="https://luizftoledo.github.io/">Luiz Fernando Toledo</a></span><p class="disclaimer">Curadoria de respostas públicas à Lei de Acesso à Informação. Cada achado aponta para o documento oficial. A seleção indica caminhos de apuração; confirmação adicional com órgãos e pessoas citadas cabe à reportagem.</p></div></footer></body></html>'''
    lines = ["A LAI que pegou", f"Edição de {date_label}", "", issue["headline"], issue["deck"],
             "", "Edição na web: https://luizftoledo.github.io/a-lai-que-pegou/edicoes/" + issue["date"] + ".html", ""]
    for item in issue["items"]:
        lines += [item["headline"], item["summary"], "Por que agora: " + item["why_now"], "Pista para apuração: " + item["pitch"], "Íntegra: " + item["source_url"]]
        if item.get("context_url"):
            lines.append("Contexto oficial: " + item["context_url"])
        lines.append("")
    if also:
        lines += ["TAMBÉM RESPONDERAM", ""]
        lines += [f"{x['headline']}. {x['summary']} {x['source_url']}" for x in also] + [""]
    if issue["precedents"]:
        lines += ["PRECEDENTES QUE AJUDAM EM OUTROS PEDIDOS", ""]
        for p in issue["precedents"]:
            lines += [p["headline"], "Antes negado: " + p["prior_denial"], "Informação a fornecer: " + p["opened_information"], "Situação: " + p["access_status"], "Interesse público: " + p["public_interest"], "Decisão: " + p["decision"], "Como usar: " + p["helps_with"], "Íntegra: " + p["source_url"]]
            if p.get("document_url"):
                lines += ["Parecer (PDF): " + p["document_url"]]
            lines += [""]
    return page, "\n".join(lines)


def main():
    if len(sys.argv) != 2:
        sys.exit("Uso: python3 scripts/publish.py issues/AAAA-MM-DD.json")
    issue_path = Path(sys.argv[1]).resolve()
    if issue_path.parent != ROOT / "issues":
        sys.exit("O arquivo da edição deve ficar em issues/.")
    issue = json.loads(issue_path.read_text(encoding="utf-8"))
    errors = validate(issue)
    if issue_path.stem != issue.get("date"):
        errors.insert(0, "O nome do arquivo deve ser igual a `date`.")
    if errors:
        sys.exit("Edição não publicada:\n- " + "\n- ".join(errors))
    page, email = render(issue)
    (DOCS / "edicoes").mkdir(parents=True, exist_ok=True)
    (DOCS / "edicoes" / f"{issue['date']}.html").write_text(page, encoding="utf-8")
    (ROOT / "outbox").mkdir(exist_ok=True)
    (ROOT / "outbox" / f"{issue['date']}.txt").write_text(email, encoding="utf-8")
    status_path = DOCS / "status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    entries = status.get("edicoes", [])
    previous = next((x for x in entries if x.get("data") == issue["date"]), None)
    # Republicar mantém o número da edição; edição nova recebe o seguinte.
    numero = previous["numero"] if previous else max([x.get("numero", 0) for x in entries] + [0]) + 1
    entries = [x for x in entries if x.get("data") != issue["date"]]
    entries.append({"numero": numero, "data": issue["date"], "file": f"edicoes/{issue['date']}.html",
                    "titulo": issue["headline"], "em_destaque": issue["deck"],
                    "e_mais": len(issue["items"]) - 1, "precedentes": len(issue["precedents"])})
    entries.sort(key=lambda x: x["data"])
    status.pop("next_run_approx", None)
    status.update({"last_run": datetime.now(timezone.utc).isoformat(), "last_run_status": "success",
                   "last_run_note": f"{len(issue['items'])} pedidos e {len(issue['precedents'])} precedentes verificados",
                   "edicoes": entries})
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Edição {issue['date']} (nº {numero}) gerada com {len(issue['items'])} itens e {len(issue['precedents'])} precedentes")


if __name__ == "__main__":
    main()
