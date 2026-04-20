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

6. **DASHBOARD EMBED** (antes do rodapé): box com CTA "abrir dashboard" linkando https://luizftoledo.github.io/lai-dashboard/ — CSS já está no template.

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
Leia `docs/edicoes/2026-04-20.html` (edição inaugural) como template EXATO. Mantenha TODO o `<style>`, paleta cream + rosa-coral + azul-petróleo, fontes Fraunces + Libre Franklin + JetBrains Mono.

Estrutura da edição nova: nameplate + varredura + destaque + "saúde/educação/segurança" (subseção) + "e mais" (subseção) + curadoria + dashboard-embed + sobre-lai + metodologia + expediente com "quem faz".

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
