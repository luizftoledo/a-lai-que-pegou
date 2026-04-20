#!/usr/bin/env python3
"""
Lê pedidos coletados em docs/data/pedidos.json, chama a API da Anthropic para
triagem + síntese jornalística, faz 3 WebSearches de curadoria e gera o HTML
da edição seguindo o template da edição inaugural.

Uso (no GitHub Action, com ANTHROPIC_API_KEY no ambiente):
    python scripts/synthesize.py
"""
import datetime
import json
import os
import re
import sys
from pathlib import Path

import anthropic

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
EDICOES = DOCS / "edicoes"
STATUS = DOCS / "status.json"
TEMPLATE_REF = EDICOES / "2026-04-20.html"
PEDIDOS = DOCS / "data" / "pedidos.json"

HOJE = datetime.date.today()
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
DIAS_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


PROMPT = """Você é curador jornalístico de uma newsletter brasileira semanal sobre pedidos reais da Lei de Acesso à Informação (LAI). Público: jornalistas.

## REGRAS DE OURO

1. **TÍTULO = LIDE com DADO CONCRETO** extraído da RESPOSTA oficial. Verbo forte + número + órgão. Não é descrição do pedido — é o achado.

2. **LINGUAGEM MASTIGADA**. Sempre que citar sigla/órgão, explique em UMA frase curta o que é e o que faz. Ex: 'SUSEP (reguladora federal do mercado de seguros)', 'EBSERH (estatal que administra os 41 hospitais universitários federais)'. Proibido: autarquia, apólice/sinistro/prêmio sem explicar, microdados, Circular nº X, sandbox regulatório, jurisprudência tributária, distorção estrutural, metragem.

3. **RANKING DE TEMAS** (priorizar): Saúde > Presidência/lobby > Ambiente > Orçamento > Militares > Segurança > Economia > Trabalho escravo > Educação. Descarte: agendamento INSS, valores a receber BACEN, cadastro SEI.

4. **MÍNIMO 6 ITENS** na edição: 1 destaque + 5 'e mais'. O primeiro é o mais forte.

5. **JAMAIS cite** Fiquem Sabendo / Don't LAI to me / qualquer newsletter de inspiração.

## DADOS DE ENTRADA

A seguir está o JSON com os pedidos LAI coletados hoje do buscalai.cgu.gov.br (entre 16/abr e 17/abr/2026):

{pedidos_json}

## TAREFA

1. Faça triagem rigorosa: só passam pedidos com lide extraível da resposta, dado concreto, não coberto por Folha/UOL/G1/Estadão/Veja.
2. Selecione 1 destaque (o mais forte) + 5 'e mais'.
3. Pro DESTAQUE, gere: kicker curto, título-lide, subtítulo, lead com letra capitular, parágrafos de contexto (USANDO verbatim da resposta quando couber), quote da resposta oficial, ficha (protocolo/órgão/datas/decisão), ângulo de pauta com perguntas.
4. Pra CADA 'e mais' (5): kicker (órgão + data), título-lide, parágrafo explicativo, ângulo de pauta, link pro pedido.

Retorne APENAS um JSON no formato (entre ```json e ```):
{{
  "destaque": {{
    "kicker": "...",
    "titulo": "...",
    "mark": "palavra/número que vai em amarelo",
    "subtitulo": "...",
    "lead": "...",
    "paragrafos": ["...", "..."],
    "quote": "citação literal da resposta",
    "quote_src": "— ÓRGÃO, resposta ao pedido NNNNN",
    "ficha": {{"protocolo": "...", "orgao": "...", "resposta": "DD/MM/YYYY", "decisao": "..."}},
    "angulo": "ângulo com perguntas concretas, fontes sugeridas",
    "url": "https://buscalai.cgu.gov.br/busca/ID"
  }},
  "e_mais": [
    {{"kicker_label": "● órgão", "kicker_data": "respondido DD/MM/YYYY",
      "titulo": "...", "mark": "...",
      "paragrafo": "...",
      "angulo": "...",
      "url": "..."}},
    ...
  ]
}}

IMPORTANTE:
- O `mark` é a palavra/número exato a ser destacado em amarelo no título (ex: "5 anos", "34%", "R$ 500 bi", "2021").
- Use HTML inline tags no título/paragrafo quando necessário (ex: <strong>, <em>), mas SEM <p> ou <div>.
- Se menos de 6 pedidos forem aprováveis, inclua os melhores (mínimo 3, e na nota do status diga "varredura seca").
- Nunca invente dado, URL, protocolo ou órgão — use só o que está no JSON."""


CURADORIA_PROMPT = """Faça 3 buscas web e retorne até 4 reportagens BRASILEIRAS recentes (últimos 7-30 dias) que citam uso explícito da Lei de Acesso à Informação (LAI).

Buscas sugeridas:
1. site:nucleo.jor.br LAI OR "acesso à informação" 2026
2. site:apublica.org "Lei de Acesso" 2026
3. "obtidos via LAI" OR "por meio da LAI" reportagem 2026

Pra cada reportagem, retorne: veiculo, data (DD/MM/YYYY), titulo, url, como_usou (1 frase explicando o método).

Retorne APENAS um JSON (entre ```json e ```):
{
  "reportagens": [
    {"veiculo": "...", "data": "DD/MM/YYYY", "titulo": "...", "url": "...", "como_usou": "..."},
    ...
  ]
}"""


def extrair_json(text):
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0]
    return json.loads(text.strip())


def sintetizar(client, pedidos):
    prompt = PROMPT.replace("{pedidos_json}", json.dumps(pedidos, ensure_ascii=False, indent=2))
    resp = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "\n".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    return extrair_json(text)


def curar_reportagens(client):
    resp = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 6}],
        messages=[{"role": "user", "content": CURADORIA_PROMPT}],
    )
    text = "\n".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    try:
        return extrair_json(text).get("reportagens", [])
    except Exception as e:
        print(f"[curadoria] erro parsing: {e}", file=sys.stderr)
        return []


def render_destaque(d):
    return f"""  <div class="section-head">○ em destaque · o mais forte</div>

  <div class="destaque">
    <div class="kicker">{d['kicker']}</div>
    <h2>{d['titulo'].replace(d.get('mark',''), f'<span class=\"mark\">{d.get(\"mark\",\"\")}</span>', 1) if d.get('mark') else d['titulo']}</h2>
    <div class="subtitle">{d['subtitulo']}</div>
    <p class="lead">{d['lead']}</p>
{"".join(f"    <p>{p}</p>" + chr(10) for p in d.get('paragrafos', []))}
    <div class="quote">"{d['quote']}" {d.get('quote_src','')}</div>
    <div class="ficha">
      <span><b>protocolo</b> {d['ficha']['protocolo']}</span>
      <span><b>órgão</b> {d['ficha']['orgao']}</span>
      <span><b>resposta</b> {d['ficha']['resposta']}</span>
      <span><b>decisão</b> {d['ficha']['decisao']}</span>
    </div>
    <div class="angulo-box">
      <b>ângulo de pauta</b>
      {d['angulo']}
    </div>
    <a class="link" href="{d['url']}" target="_blank">→ ver pedido original</a>
  </div>
"""


def render_item(item):
    titulo = item['titulo']
    if item.get('mark'):
        titulo = titulo.replace(item['mark'], f'<span class="mark">{item["mark"]}</span>', 1)
    return f"""  <div class="item">
    <div class="kicker"><b>{item['kicker_label']}</b> · {item['kicker_data']}</div>
    <h3>{titulo}</h3>
    <p>{item['paragrafo']}</p>
    <p class="angulo"><strong>Ângulo:</strong> {item['angulo']}</p>
    <a class="link" href="{item['url']}" target="_blank">→ ver pedido</a>
  </div>
"""


def render_curadoria(reportagens):
    if not reportagens:
        return ""
    itens = "".join(f"""    <div class="reportagem">
      <div class="rep-meta"><b>{r['veiculo']}</b> · {r['data']}</div>
      <a class="rep-titulo" href="{r['url']}" target="_blank">{r['titulo']}</a>
      <div class="rep-como"><b>método:</b> {r['como_usou']}</div>
    </div>
""" for r in reportagens)
    return f"""  <div class="curadoria">
    <h2>○ reportagens que usaram a LAI</h2>
    <div class="sub">como o jornalismo brasileiro tem usado a Lei de Acesso à Informação nas últimas semanas</div>
{itens}  </div>

  <div class="dashboard-embed">
    <div class="dashboard-label">○ volume de pedidos em tempo real</div>
    <p class="dashboard-desc">Um painel que acompanha o atendimento da LAI no governo federal — dados atualizados pela CGU.</p>
    <a class="dashboard-cta" href="https://luizftoledo.github.io/lai-dashboard/" target="_blank">→ abrir dashboard</a>
  </div>
"""


def montar_html(data, sintese, reportagens, num_edicao):
    base = TEMPLATE_REF.read_text(encoding="utf-8")
    # extrai bloco <head>...</head> + <style>...</style> + <nav> até <body>
    head_end = base.find("<body>") + len("<body>")
    head = base[:head_end]

    data_iso = data.isoformat()
    data_display = f"{DIAS_SEMANA[data.weekday()]} · {data.day:02d} de {['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'][data.month-1]} de {data.year}"

    nome = f"edi&ccedil;&atilde;o #{num_edicao:03d}"

    corpo_itens = "".join(render_item(i) for i in sintese.get("e_mais", []))

    corpo = f"""
<div class="container">
  <a href="../index.html" class="back-link">← arquivo de edições</a>

  <div class="nameplate">
    <div class="edition-meta">
      <span class="num">edição #{num_edicao:03d}</span>
      <span>{data_display}</span>
    </div>
    <div class="logo-text">A <span class="lai-wrap">LAI</span> <span class="que">que</span></div>
    <div class="logo-subtext">pegou</div>
  </div>

  <div class="varredura">
    <b>○ varredura desta edição</b>
    <ul>
      <li>varredura: {data.day:02d} de {['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'][data.month-1]} de {data.year}</li>
      <li>fonte: buscalai.cgu.gov.br · pedidos dos últimos 90 dias</li>
      <li>pedidos lidos: {len(json.load(open(PEDIDOS)))} · aprovados nesta edição: {1 + len(sintese.get('e_mais', []))}</li>
      <li>curadoria externa: {len(reportagens)} reportagens recentes com uso de LAI</li>
      <li>próxima varredura automática: segunda, 08h Londres</li>
    </ul>
  </div>

{render_destaque(sintese['destaque'])}

  <div class="section-head">○ e mais · outros pedidos da semana</div>

{corpo_itens}
{render_curadoria(reportagens)}

  <div class="sobre-lai">
    <h3>○ o que é a LAI</h3>
    <p>A LAI é a <strong>Lei de Acesso à Informação</strong> (Lei 12.527, de 2011), que dá a qualquer cidadão o direito de pedir informações a qualquer órgão público — e obriga o governo a responder em até 20 dias, prorrogáveis por mais 10.</p>
    <p>Dizem que no Brasil há leis que não pegam. <strong>Essa pegou</strong> — já são mais de 1 milhão de pedidos enviados ao governo federal desde que a lei entrou em vigor em maio de 2012, segundo a Controladoria-Geral da União.</p>
  </div>

  <div class="metodologia">
    <div class="label">○ como a gente coleta</div>
    <ul>
      <li>Toda segunda de manhã, uma varredura automática entra no Busca LAI (buscalai.cgu.gov.br), sistema público da CGU que reúne pedidos feitos ao governo federal e as respostas dadas.</li>
      <li>Pega os pedidos mais recentes em 9 temas prioritários: saúde, lobby e agendas, meio ambiente, orçamento, militares, segurança pública, economia, trabalho escravo e educação.</li>
      <li>Abre cada pedido e lê a resposta oficial na íntegra.</li>
      <li>Descarta o ruído: agendamento no INSS, valor a receber no BACEN, cadastro de sistema etc.</li>
      <li>Entram na edição só os que têm dado concreto e potencial de virar pauta.</li>
      <li>Ao fim, uma curadoria com reportagens brasileiras que usaram a LAI na semana.</li>
    </ul>
  </div>

  <div class="expediente">
    <p>edição #{num_edicao:03d} · {data.day:02d}.{MESES[data.month-1]}.{data.year}</p>
    <p>próxima varredura: segunda, 08h Londres</p>
    <p class="quem-faz">○ quem faz · <a href="https://luizftoledo.github.io" target="_blank">luizftoledo.github.io</a> · <a href="https://datafixers.org" target="_blank">datafixers.org</a></p>
  </div>

</div>
</body>
</html>"""

    # CSS extra pro dashboard-embed
    dashboard_css = """
  .dashboard-embed {
    margin-top: 24px; padding: 24px 28px;
    background: linear-gradient(135deg, var(--paper-2) 0%, var(--paper) 100%);
    border: 1px solid var(--line); border-left: 3px solid var(--stamp);
  }
  .dashboard-embed .dashboard-label {
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    letter-spacing: 3px; text-transform: uppercase;
    color: var(--stamp); font-weight: 700; margin-bottom: 10px;
  }
  .dashboard-embed .dashboard-desc {
    font-family: 'Fraunces', serif; font-size: 15px; color: var(--ink-2);
    margin-bottom: 14px; font-style: italic;
  }
  .dashboard-embed .dashboard-cta {
    display: inline-block; padding: 10px 18px;
    background: var(--ink); color: var(--paper);
    text-decoration: none; font-family: 'JetBrains Mono', monospace;
    font-size: 12px; letter-spacing: 2px; text-transform: uppercase;
    font-weight: 600;
  }
  .dashboard-embed .dashboard-cta:hover { background: var(--stamp); }
"""
    head = head.replace("</style>", dashboard_css + "</style>")
    return head + corpo


def atualizar_status(num, titulo, em_destaque, qtd_itens, qtd_reportagens, status="success", note=""):
    data = json.loads(STATUS.read_text())
    today = HOJE.isoformat()
    entry = {
        "numero": num,
        "data": today,
        "file": f"edicoes/{today}.html",
        "titulo": titulo,
        "em_destaque": em_destaque,
        "e_mais": qtd_itens - 1,
        "reportagens_curadas": qtd_reportagens,
    }
    edicoes = [e for e in data.get("edicoes", []) if e.get("data") != today]
    edicoes.append(entry)
    data["edicoes"] = edicoes
    data["last_run"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    data["last_run_status"] = status
    data["last_run_note"] = note or f"edição #{num} · {qtd_itens} itens · {qtd_reportagens} reportagens"
    proxima = HOJE + datetime.timedelta(days=(7 - HOJE.weekday()) % 7 or 7)
    data["next_run_approx"] = f"{proxima.isoformat()}T08:00:00+01:00"
    STATUS.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    if not PEDIDOS.exists():
        print("[synthesize] docs/data/pedidos.json não existe — abortando", file=sys.stderr)
        sys.exit(2)

    pedidos = json.loads(PEDIDOS.read_text())
    if len(pedidos) < 5:
        print(f"[synthesize] só {len(pedidos)} pedidos — abortando", file=sys.stderr)
        sys.exit(2)

    client = anthropic.Anthropic()
    print(f"[synthesize] {len(pedidos)} pedidos carregados")

    sintese = sintetizar(client, pedidos)
    print(f"[synthesize] destaque: {sintese['destaque']['titulo'][:80]}")
    print(f"[synthesize] e mais: {len(sintese.get('e_mais', []))} itens")

    reportagens = curar_reportagens(client)
    print(f"[synthesize] curadoria: {len(reportagens)} reportagens")

    status = json.loads(STATUS.read_text())
    num_edicao = (status.get("edicoes", [{}])[-1].get("numero", 0) or 0) + 1

    html = montar_html(HOJE, sintese, reportagens, num_edicao)
    target = EDICOES / f"{HOJE.isoformat()}.html"
    target.write_text(html, encoding="utf-8")
    print(f"[synthesize] HTML gerado: {target}")

    atualizar_status(
        num=num_edicao,
        titulo=sintese['destaque']['titulo'][:120],
        em_destaque=sintese['destaque']['subtitulo'][:140],
        qtd_itens=1 + len(sintese.get('e_mais', [])),
        qtd_reportagens=len(reportagens),
    )
    print(f"[synthesize] status.json atualizado — edição #{num_edicao}")


if __name__ == "__main__":
    main()
