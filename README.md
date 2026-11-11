# A LAI que pegou

Newsletter de curadoria jornalística de respostas públicas à Lei de Acesso à
Informação, publicada em https://luizftoledo.github.io/a-lai-que-pegou/.

Os critérios de seleção estão em [CRITERIOS.md](CRITERIOS.md). O formato do
arquivo de cada edição está em [issues/README.md](issues/README.md).

## Fontes, em ordem

1. **Dados abertos de pedidos** (`dadosabertos-download.cgu.gov.br`, ZIP anual
   atualizado toda noite). Traz pedido, resposta (até 14 mil caracteres),
   decisão, links dos anexos e recursos. É a base da triagem e não depende da
   API. `scripts/triagem.py` grava `data/candidatos.json`; o GitHub Actions
   roda isso às segundas, 05:30 UTC (`.github/workflows/triagem.yml`).
2. **API pública do InformaBR** (`api-laibr.cgu.gov.br`). Texto integral e
   anexos. Devolve 403 a partir de alguns provedores de nuvem; de conexão
   doméstica responde. `scripts/detalhe.py ID` tenta a API e, se falhar, lê o
   mesmo pedido nos dados abertos, informando a via usada.
3. **Página do InformaBR ou do BuscaLAI no navegador**, para anexos e para
   respostas cortadas nos dados abertos.

## Rotina editorial

1. Ler `data/candidatos.json`. Se `fonte.desatualizada` for verdadeiro ou o
   arquivo for de outra semana, rodar `python3 scripts/triagem.py`.
2. Percorrer os candidatos além dos primeiros; `pontos_triagem` só ordena a
   leitura. Para cada pista, ler pedido e resposta com
   `python3 scripts/detalhe.py ID` e os anexos acessíveis.
3. Pontuar cada pista pelos cinco eixos de CRITERIOS.md, com motivo escrito.
   Conferir no noticiário se o fato já saiu com o mesmo dado.
4. Para precedentes, partir de `recursos` em `data/candidatos.json` e ler a
   decisão integral.
5. Montar `issues/AAAA-MM-DD.json` e rodar
   `python3 scripts/publish.py issues/AAAA-MM-DD.json`. O script recusa a
   edição que não cumpre os critérios e lista os motivos.
6. Rever a página e o texto de e-mail gerados, fazer `git push origin main` e
   confirmar a edição no endereço público.
7. Enviar a edição para `lta2119@columbia.edu` com a capa
   `docs/assets/capa-lai.gif` no início, conferir Enviados e registrar
   `outbox/AAAA-MM-DD.sent`. Antes de repetir um envio incerto, conferir
   Enviados.

## Quando uma fonte falha

- **API ou página com 403 ou fora do ar:** seguir pelos dados abertos. Entram
  os itens cujo texto completo está na base (`resposta_cortada` falso) e cujos
  fatos publicados constam no texto da resposta. Registrar
  `verificado_por: dados_abertos` e, em `attachment_review`, que o anexo não
  foi aberto.
- **Dados abertos indisponíveis ou mais de 3 dias atrasados:** usar a API ou o
  navegador, de uma máquina em que respondam.
- **Nenhuma via disponível:**
  `python3 scripts/rodada_sem_edicao.py AAAA-MM-DD fonte_indisponivel "o que falhou"`.
- **Fontes disponíveis, nenhum pedido com 8 pontos:**
  `python3 scripts/rodada_sem_edicao.py AAAA-MM-DD sem_pauta "quantos lidos, maior pontuação"`.

O registro atualiza `docs/status.json`, e a página inicial informa o motivo.
Uma rodada sem edição não altera edições publicadas.

## Frequência

Revisão semanal às segundas-feiras, 8h (Europe/London).
