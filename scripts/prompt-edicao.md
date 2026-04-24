Você vai gerar a edição da newsletter "A LAI que pegou" desta semana. Público: jornalistas brasileiros.

## REGRAS DE OURO

1. **TÍTULO = LIDE COM DADO CONCRETO** extraído da RESPOSTA oficial do pedido. Não é descrição do pedido — é o achado. Verbo forte + número + órgão.

2. **LINGUAGEM MASTIGADA**. Sempre que citar sigla/órgão, explique em UMA frase:
   - SUSEP → "reguladora federal do mercado de seguros"
   - EBSERH → "estatal que administra os 41 hospitais universitários federais"
   - TCU → "Tribunal de Contas da União, que fiscaliza gastos públicos"
   - CGU → "Controladoria-Geral da União, que fiscaliza a LAI no governo federal"
   - INSS → "órgão que paga aposentadorias e benefícios"
   - Ibama, Anvisa, ANS, MEC, Funai, ICMBio — explicar sempre.
   PROIBIDO sem traduzir: autarquia, apólice/sinistro/prêmio, microdados, "Circular nº X", "Solução de Consulta SRRF10", "jurisprudência tributária", sandbox regulatório, integralização, distorção estrutural, metragem.

3. **RANKING DE TEMAS** (priorizar nesta ordem): Saúde > Presidência/lobby > Meio ambiente > Orçamento > Militares > Segurança > Economia > Trabalho escravo > Educação.
   Descartar: agendamento INSS, valores a receber BACEN, cadastro SEI, carteira de profissional.

4. **MÍNIMO 6 ITENS**: 1 destaque + 5 "e mais". O primeiro é o mais forte.

5. **CURADORIA FINAL**: 3-5 reportagens brasileiras com LAI da última semana. Fazer 3 WebSearches (site:nucleo.jor.br LAI, site:apublica.org "Lei de Acesso", "obtidos via LAI" 2026).

6. **MONITOR DA LAI** (box com stats + CTA). Antes de gerar a seção, puxe stats frescas do dashboard:

```bash
curl -sk https://luizftoledo.github.io/lai-dashboard/data/metadata.json | python3 -c "import sys,json; o=json.load(sys.stdin)['overall']; print(o)"
curl -sk https://luizftoledo.github.io/lai-dashboard/data/report_data.json | python3 -c "import sys,json; r=json.load(sys.stdin); print('top_negador:', sorted([o for o in r['org_ranking'] if o['total_requests']>15000], key=lambda x: -x['denied_rate'])[0])"
```

Use os números no quadro `.stats-mini` (3 colunas):
- total de pedidos desde 2012 (formato "1,68 mi")
- taxa de negação geral (%)
- órgão com maior taxa de negação entre os de alto volume (nome + %)

Estrutura HTML do bloco, usando o CSS já existente no template:
```html
<div class="dashboard-embed">
  <div class="label">○ ferramenta aberta</div>
  <h3>Monitor da LAI</h3>
  <p class="monitor-sub"><em>Veja quem está negando mais o acesso à informação e quem está usando mais o dispositivo de sigilo.</em></p>
  <div class="stats-mini">
    <div><div class="stat-num">X,XX mi</div><div class="stat-label">pedidos enviados ao governo federal desde 2012</div></div>
    <div><div class="stat-num">X,X%</div><div class="stat-label">das respostas são negativas</div></div>
    <div><div class="stat-num">X,X%</div><div class="stat-label">é a taxa de negação do [ÓRGÃO] — a maior entre órgãos com + de 15 mil pedidos</div></div>
  </div>
  <p>Todas as respostas que viraram matéria — e as que ficaram de fora — estão no dashboard público. Dá para filtrar por órgão, tema, data e decisão. Atualiza toda segunda, junto com a newsletter.</p>
  <a class="cta" href="https://luizftoledo.github.io/lai-dashboard/" target="_blank">abrir dashboard →</a>
</div>
```

## PASSOS

### 1. Ler pedidos coletados
Abra `docs/data/pedidos.json`. Confirme quantos pedidos tem. Se menos de 5: atualize `docs/status.json` com `last_run_status="warning"`, commite e pare.

### 2. Triagem
Para cada pedido, aplique critérios cumulativos:
- Tema está entre TOP 9
- Lide com número/fato extraível da RESPOSTA oficial
- Não coberto por Folha/UOL/G1/Estadão/Veja com mesmo ângulo
- Não é pergunta pessoal trivial

Selecione 1 destaque (lide mais forte) + 5 "e mais". Ordene por força. Diversifique temas.

### 3. Curadoria externa
3 WebSearches conforme regra 5. Reúna 3-5 reportagens com título, veículo, data, URL, "como usou".

### 4. Gerar HTML
Leia `docs/edicoes/2026-04-20.html` (edição inaugural) como template EXATO. Mantenha TODO o `<style>`, paleta off-white + mint + teal + ink preto (aliada ao datafixers.org), fontes Fraunces + Inter + JetBrains Mono.

Estrutura da edição nova, nesta ORDEM:
1. nameplate (logo + data)
2. **descritivo** — bloco com `.descritivo` logo após o nameplate, com UM parágrafo italic explicando o que é a newsletter (texto fixo): "A LAI que pegou é uma newsletter semanal que vasculha o Busca LAI — sistema público da Controladoria-Geral da União com todos os pedidos de acesso à informação feitos ao governo federal. Destacamos o que o governo respondeu, o que tentou esconder, e o que vale virar pauta."
3. destaque
4. "saúde/educação/segurança" (subseção)
5. "e mais" (subseção)
6. curadoria de reportagens
7. dashboard-embed
8. sobre-lai
9. metodologia
10. **varredura** — metadados da varredura aqui PRÓXIMO do fim (não no topo)
11. expediente com "quem faz"

O CSS `.descritivo` já está definido no template (edição inaugural).

Linguagem de cada parágrafo: mastigada. Jornalista cansado precisa entender em 30 segundos.

Escreva em `docs/edicoes/YYYY-MM-DD.html` usando **a data de HOJE**, obtida via bash `date +%Y-%m-%d`. NÃO use "próxima segunda" nem data futura — use exatamente a data do dia em que este script está rodando. Dentro do HTML (header, varredura, expediente), use também a data de hoje. Número da edição = próximo em `docs/status.json`.

### 5. Atualizar status.json
Adicione nova entrada na lista `edicoes` com: numero, data, file, titulo (=lide do destaque, <= 120 chars), em_destaque (resumo 1 linha com número), e_mais (int), reportagens_curadas (int). Atualize `last_run` (ISO UTC agora), `last_run_status="success"`, `last_run_note`, `next_run_approx` (próxima segunda 08h+01:00).

## REGRAS CRÍTICAS

- JAMAIS cite "Fiquem Sabendo", "Don't LAI to me" ou inspirações.
- Nunca invente dado, protocolo, URL ou órgão — use somente o que está no JSON.
- Sempre traduzir siglas (regra 2 é a mais crítica).
- Mínimo 6 itens.
- Ao final, responda APENAS: número da edição, lide do destaque, quantidade de itens, quantidade de reportagens curadas. Nada mais. Não commite — o script externo faz o commit.
