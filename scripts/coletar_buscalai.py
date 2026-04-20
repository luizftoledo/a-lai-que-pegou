#!/usr/bin/env python3
"""
Coleta pedidos LAI recentes do buscalai.cgu.gov.br usando Playwright.
Uso: python3 scripts/coletar_buscalai.py [dias] [quantidade]
Gera /tmp/pedidos_detalhados.json com metadados + pedido + resposta completos.
"""
import asyncio, json, re, sys
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright

DIAS = int(sys.argv[1]) if len(sys.argv) > 1 else 90
ALVO = int(sys.argv[2]) if len(sys.argv) > 2 else 25
LIMITE = datetime.now() - timedelta(days=DIAS)

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
        out[k] = m.group(1).strip()[:4000] if m else ""
    return out

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(locale="pt-BR")
        page = await ctx.new_page()
        await page.goto("https://buscalai.cgu.gov.br/", wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(3000)
        try:
            await page.get_by_role("button", name="Aceitar Todos").click(timeout=5000)
            await page.wait_for_timeout(1000)
        except: pass
        await page.locator("button[type=submit].br-button.primary").click()
        await page.wait_for_timeout(5000)
        await page.locator("select").first.select_option(value="maisRecentes")
        await page.wait_for_timeout(5000)

        urls = []
        for pagina in range(1, 8):
            links = page.locator("a:has-text('Ver pedido')")
            count = await links.count()
            for i in range(count):
                href = await links.nth(i).get_attribute("href")
                if href:
                    full = ("https://buscalai.cgu.gov.br" + href) if href.startswith("/") else href
                    if full not in urls:
                        urls.append(full)
            print(f"[lista pag {pagina}] acumulado {len(urls)} URLs", file=sys.stderr)
            if len(urls) >= ALVO * 2:
                break
            try:
                prox = page.locator("nav button").filter(has_text=str(pagina+1)).first
                await prox.click(timeout=3000)
                await page.wait_for_timeout(4000)
            except Exception as e:
                print(f"[pag {pagina+1}] sem próxima: {str(e)[:60]}", file=sys.stderr)
                break

        detalhes = []
        for i, u in enumerate(urls[:ALVO]):
            print(f"[{i+1}/{min(ALVO,len(urls))}] {u}", file=sys.stderr)
            try:
                await page.goto(u, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2500)
                txt = await page.inner_text("body")
                d = extrair(txt)
                d["url"] = u
                if d.get("data_resposta"):
                    try:
                        dt = datetime.strptime(d["data_resposta"], "%d/%m/%Y")
                        if dt >= LIMITE:
                            detalhes.append(d)
                    except: pass
            except Exception as e:
                print(f"  erro: {str(e)[:100]}", file=sys.stderr)

        out = Path("/tmp/pedidos_detalhados.json")
        out.write_text(json.dumps(detalhes, ensure_ascii=False, indent=2))
        print(f"[fim] {len(detalhes)} pedidos gravados em {out}", file=sys.stderr)
        await browser.close()

asyncio.run(main())
