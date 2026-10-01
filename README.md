# A LAI que pegou

Newsletter de curadoria jornalística de respostas públicas à Lei de Acesso à
Informação, publicada em https://luizftoledo.github.io/a-lai-que-pegou/.

## Rotina editorial

1. Verificar a data efetiva e a disponibilidade de [BuscaLAI](https://buscalai.cgu.gov.br/), [Busca Precedentes](https://www.gov.br/cgu/pt-br/acesso-a-informacao/dados-abertos/arquivos/busca-de-precedentes) e [dados abertos de pedidos](https://falabr.cgu.gov.br/web/dadosabertoslai). A base de dados abertos é uma pista de triagem; ela não substitui a resposta integral.
2. Buscar pedidos **respondidos recentemente** em muitos temas e resultados; não parar na primeira leva. Ler texto completo e anexos públicos. Priorizar fatos ou dados novos, ângulos originais, relevância para o noticiário e apuração possível. Conferir se a história já foi publicada com o mesmo ângulo. Uma negativa só entra quando a recusa, por si, for excepcional e claramente noticiável; não usá-la para completar a edição ou abrir a newsletter diante de uma descoberta concreta melhor.
3. Ler as decisões integrais antes de explicar um precedente. Descrever o que foi decidido e como usar a tese em outro pedido, sem transformar caso específico em regra geral.
4. Continuar a triagem até reunir os melhores achados verificáveis da rodada. Registrar cerca de seis, podendo publicar menos quando a verificação não sustentar seis. Abrir com a descoberta mais forte, que também deve orientar o título da edição. Registrar pelo menos um precedente. Guardar evidência, protocolo e link em `issues/AAAA-MM-DD.json`.
5. `python3 scripts/publish.py issues/AAAA-MM-DD.json` valida o registro e gera a página e a versão para e-mail. Rever os dois arquivos gerados antes de `git push origin main`.
6. Confirmar que a edição responde no endereço público. Só então compor a mesma edição com títulos, seções e links no Mail deste Mac, inserir `docs/assets/capa-lai.gif` no início como capa animada, enviar para `lta2119@columbia.edu`, conferir a pasta Enviados e registrar `outbox/AAAA-MM-DD.sent`. Antes de repetir uma tentativa incerta, conferir Enviados para evitar cópia duplicada.

Não há publicação automática a partir de resumos de busca. Uma falha de fonte
encerra a rodada com registro de erro e sem alterar a última edição válida.

## Frequência

Revisão diária de 1º a 7 de outubro de 2026. A partir de 12 de outubro, revisão
às segundas-feiras. O agendamento editorial é gerenciado no Codex; o antigo
`launchd` e a coleta semanal por GitHub Actions foram desativados.
