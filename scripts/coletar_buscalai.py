#!/usr/bin/env python3
"""
Coleta pedidos LAI recentes do buscalai.cgu.gov.br via Playwright.
Faz buscas dirigidas por tema (ranking dos temas que mais funcionam),
abre cada pedido e extrai protocolo/órgão/pedido/resposta completos.

Uso: python3 scripts/coletar_buscalai.py [dias] [alvo_total]
Gera /tmp/pedidos_detalhados.json
"""
import asyncio, json, re, sys
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright

DIAS = int(sys.argv[1]) if len(sys.argv) > 1 else 90
ALVO = int(sys.argv[2]) if len(sys.argv) > 2 else 40
LIMITE = datetime.now() - timedelta(days=DIAS)

# Ranking de temas baseado em análise de 193 edições de newsletter de referência (2019-2026)
# Ordem = força do tema + keywords pra busca no buscalai
BUSCAS_POR_TEMA = [
    # top 1 · saúde (19.7% das edições)
    ("saude", ["SUS", "hospital", "medicamento", "vacina", "Anvisa", "ANS", "INCA"]),
    # top 2 · presidência/lobby/agendas (18.1%)
    ("lobby_agendas", ["reuniões", "agenda", "Planalto", "cartão corporativo"]),
    # top 3 · meio ambiente (15.5%)
    ("ambiente", ["Ibama", "ICMBio", "desmatamento", "garimpo", "licenciamento"]),
    # top 4 · orçamento/gastos (14.5%)
    ("orcamento", ["orçamento", "contratação", "emenda", "renúncia fiscal"]),
    # top 5 · militares/defesa (14.0%)
    ("militares", ["Exército", "Marinha", "militares", "Defesa"]),
    # top 6 · segurança/polícia (13.5%)
    ("seguranca", ["Polícia Federal", "PRF", "armas", "droga", "presídio"]),
    # top 7 · economia/multas (9.3%)
    ("economia", ["Banco Central", "BACEN", "multas", "sanção"]),
    # nicho · trabalho escravo (5.7%) — alta potência jornalística
    ("trab_escravo", ["trabalho escravo", "lista suja", "resgatados"]),
    # nicho · educação (3.6%) — sub-explorado
    ("educacao", ["MEC", "universidade", "Enem", "FNDE"]),
]

def extrair(txt):
    out = {}
    for (k, regex) in [
        ("protocolo", r"Número do protocolo:\s*([\d.\-/]+)"),
        ("orgao", r"Órgão:\s*([^\n]+)"),
        ("data_pedido", r"Data Pedido:\s*([\d/]+)"),
        ("assunto", r"Assunto:\s*([^\n]+)"),
        ("subassunto", r"Subassunto:\s*([^\n]+)"),
        ("pedido", r"Pedido:\s*(.+?)(?=Resumo:|Este resumo foi gerado|Resposta:|\Z)"),
        ("resumo_ia", r"Resumo:\s*(.+?)(?=Este resumo foi gerado|Entenda mais|Resposta:|\Z)"),
        ("resposta", r"Resposta:\s*(.+?)(?=Data de resposta|Decisão:|A Busca LAI preza|\Z)"),
        ("data_resposta", r"Data de resposta ao pedido:\s*([\d/]+)"),
        ("decisao", r"Decisão:\s*([^\n]+)"),
    ]:
        m = re.search(regex, txt, re.DOTALL)
        out[k] = m.group(1).strip()[:5000] if m else ""
    return out

async def buscar_termo(page, termo):
    """Home → digita termo → busca → ordena por recentes → extrai URLs."""
    await page.goto("https://buscalai.cgu.gov.br/", wait_until="networkidle", timeout=45000)
    await page.wait_for_timeout(2500)
    try:
        await page.get_by_role("button", name="Aceitar Todos").click(timeout=3000)
        await page.wait_for_timeout(600)
    except: pass
    # limpar e digitar termo no campo de busca
    try:
        inp = page.locator("input[type=text], input[type=search]").first
        await inp.click()
        await inp.press("Control+A")
        await inp.press("Delete")
        await inp.type(termo, delay=30)
        await page.wait_for_timeout(500)
    except Exception as e:
        print(f"  erro input: {e}", file=sys.stderr)
        return []
    # submeter
    try:
        await page.locator("button[type=submit].br-button.primary").click(timeout=5000)
        await page.wait_for_timeout(5000)
    except Exception as e:
        print(f"  erro submit: {e}", file=sys.stderr)
        return []
    # ordenar por mais recentes
    try:
        await page.locator("select").first.select_option(value="maisRecentes")
        await page.wait_for_timeout(4000)
    except: pass
    links = page.locator("a:has-text('Ver pedido')")
    count = await links.count()
    urls = []
    for i in range(count):
        href = await links.nth(i).get_attribute("href")
        if href:
            full = ("https://buscalai.cgu.gov.br" + href) if href.startswith("/") else href
            urls.append(full)
    return urls

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(locale="pt-BR")
        page = await ctx.new_page()
        urls_por_tema = {}
        for tema, termos in BUSCAS_POR_TEMA:
            for termo in termos[:2]:  # 2 termos por tema pra não demorar
                urls = await buscar_termo(page, termo)
                print(f"[{tema}:{termo!r}] +{len(urls)}", file=sys.stderr)
                for u in urls:
                    if u not in urls_por_tema:
                        urls_por_tema[u] = tema
                if len(urls_por_tema) >= ALVO * 2:
                    break
            if len(urls_por_tema) >= ALVO * 2:
                break
        print(f"[total URLs] {len(urls_por_tema)}", file=sys.stderr)
        detalhes = []
        for i, (u, tema) in enumerate(urls_por_tema.items()):
            if len(detalhes) >= ALVO:
                break
            print(f"[{i+1}/{len(urls_por_tema)}] {tema} :: {u}", file=sys.stderr)
            try:
                await page.goto(u, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2500)
                txt = await page.inner_text("body")
                d = extrair(txt)
                d["url"] = u
                d["tema"] = tema
                if d.get("resposta") and d.get("data_resposta"):
                    try:
                        dt = datetime.strptime(d["data_resposta"], "%d/%m/%Y")
                        if dt >= LIMITE:
                            detalhes.append(d)
                    except: pass
            except Exception as e:
                print(f"  erro: {str(e)[:80]}", file=sys.stderr)
        out = Path("/tmp/pedidos_detalhados.json")
        out.write_text(json.dumps(detalhes, ensure_ascii=False, indent=2))
        from collections import Counter
        c = Counter(d.get("tema","?") for d in detalhes)
        print(f"[fim] {len(detalhes)} pedidos · por tema: {dict(c)}", file=sys.stderr)
        await browser.close()

asyncio.run(main())
