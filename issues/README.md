# Pauta e evidências por edição

Crie um JSON `AAAA-MM-DD.json` com `date`, `headline`, `deck`, `items` e `precedents`.
O `headline` da edição deve ser igual ao primeiro item de `items`: a pauta mais forte
e noticiável. A seção de `precedents` é sempre a última, depois de todos os itens.

Cada item de `items` precisa de: `headline`, `summary`, `why_now`, `pitch`,
`source_url`, `protocol`, `response_date` (AAAA-MM-DD), `evidence` (passagem
literal ou números exatos da resposta), `attachment_review` (o que foi examinado,
ou "Sem anexo público") e, quando houver, `attachment_url`.

Use `precedents: []` se nenhuma decisão examinada abrir uma informação
concreta de interesse público antes negada. Não preencha a seção com questões
apenas procedimentais. Quando houver um precedente, registre `headline`,
`prior_denial` (o que o órgão negava e por quê), `opened_information` (a
informação específica liberada), `public_interest`, `access_status` (`entrega
determinada` ou `entrega confirmada`), `decision`, `helps_with`, `source_url`,
`protocol`, `decision_date` (AAAA-MM-DD) e `evidence` (trecho decisivo do
parecer integral). Confirme separadamente se a ordem já foi cumprida.

Os campos `evidence` e `attachment_review` são o registro de verificação da
curadoria. Só publique informação que a fonte oficial sustenta. Se a resposta
ou o anexo não estiver acessível, não use esse achado.
