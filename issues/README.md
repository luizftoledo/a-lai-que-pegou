# Pauta e evidências por edição

Crie um JSON `AAAA-MM-DD.json` com `date`, `headline`, `deck`, `items` e `precedents`.

Cada item de `items` precisa de: `headline`, `summary`, `why_now`, `pitch`,
`source_url`, `protocol`, `response_date` (AAAA-MM-DD), `evidence` (passagem
literal ou números exatos da resposta), `attachment_review` (o que foi examinado,
ou "Sem anexo público") e, quando houver, `attachment_url`.

Cada precedente precisa de: `headline`, `decision`, `helps_with`, `source_url`,
`protocol`, `decision_date` (AAAA-MM-DD) e `evidence` (trecho decisivo).

Os campos `evidence` e `attachment_review` são o registro de verificação da
curadoria. Só publique informação que a fonte oficial sustenta. Se a resposta
ou o anexo não estiver acessível, não use esse achado.
