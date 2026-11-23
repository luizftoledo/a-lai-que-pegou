# Regras de operação — A LAI que pegou (Codex)

Estas regras valem para toda rodada semanal ou manual no repositório `/Users/luizfernandotoledo/a-lai-que-pegou` e prevalecem sobre instruções antigas (como prompts de outubro de 2026).

## 1. Branch, ambiente e recuperação de atraso

- **Sempre operar em `main`:** começar com `git checkout main && git pull --ff-only`. Nunca produzir ou publicar a partir de branches antigas (ex.: `triagem-dados-abertos-criterios`).
- **Python:** usar `/usr/bin/python3` para todos os scripts e testes (evita divergência de pacotes no PATH).
- **Recuperação de atraso:** a rodada padrão é toda segunda-feira às 08h (`Europe/London`). Se o Mac estava em repouso ou o Codex fechado na segunda de manhã, recuperar automaticamente na próxima janela aberta da mesma semana, desde que `issues/<data-da-edicao>.json` ainda não tenha sido publicada nesta semana. Se já existe edição publicada e `outbox/<data>.sent` registrado para a semana corrente, encerrar em silêncio.

## 2. Triagem e seleção editorial (ordem obrigatória)

1. Ler `CRITERIOS.md` e `README.md`.
2. Conferir `data/candidatos.json`. Se `fonte.desatualizada` for `true` ou o arquivo for de outra semana, rodar `/usr/bin/python3 scripts/triagem.py` (usando o ZIP anual dos dados abertos da CGU em `.cache/`).
3. Percorrer candidatos além dos primeiros (`pontos_triagem` apenas ordena a leitura). Para cada pista, ler pedido e resposta integral com `/usr/bin/python3 scripts/detalhe.py ID` e conferir os anexos acessíveis.
4. Pontuar cada candidato nos cinco eixos de `CRITERIOS.md` (`alcance`, `efeito`, `solidez`, `atualidade`, `clareza`, 0 a 3) com motivo escrito apoiado na resposta e checagem de cobertura no noticiário (`nao_coberto` ou `coberto_sem_o_dado`; `bem_coberto` fica fora).
5. **Quantidade mínima e máxima:** publicar de **5 a 6 achados qualificados** (8+ pontos; abertura com 11+ pontos, ou ao menos dois itens de 8+ com abertura tendo `alcance >= 2` e `clareza >= 2`). Nunca completar a edição com material fraco ou negativas fora da regra (`alcance == 3` e `efeito == 3`). Se após ampliar a busca não houver 5 qualificados, registrar com `/usr/bin/python3 scripts/rodada_sem_edicao.py` e preservar a última edição válida.
6. **Precedente obrigatório:** toda edição deve trazer ao menos **1 precedente validado** da CGU ou CMRI (parecer integral e decisão assinada lidos, protocolo inédito nas edições anteriores), sempre ao final, nunca na manchete.

## 3. Arquivamento de fontes, publicação e testes (obrigatórios antes do push)

1. Montar `issues/AAAA-MM-DD.json` (sem siglas fora de `SIGLAS_LIVRES` no título, até 90 caracteres, no máximo 2 números, sem linguagem promocional ou slogans).
2. Gerar as cópias verificáveis de pedido e resposta da base da CGU:
   `/usr/bin/python3 scripts/arquivar_fontes.py issues/AAAA-MM-DD.json .cache/Arquivos_csv_ANO.zip`
   (Suprimir assinatura pessoal do solicitante via `"privacy_omit_request_signature": true` quando necessário.)
3. Validar e renderizar a página da edição e o texto da newsletter:
   `/usr/bin/python3 scripts/publish.py issues/AAAA-MM-DD.json`
4. Rodar a suíte de testes:
   `/usr/bin/python3 -m unittest discover -s tests -q`
   Não fazer push se qualquer teste falhar.
5. Fazer commit e `git push origin main` (apenas arquivos da edição/site; nunca commitar rascunhos temporários como `Untitled.ipynb`).

## 4. Conferência ao vivo e envio (sem duplicatas)

1. **Conferir o site publicado:** validar HTTP 200 **e conteúdo real** (não tela vazia de SPA) em `https://luizftoledo.github.io/a-lai-que-pegou/`, na página da edição (`edicoes/AAAA-MM-DD.html`) e nas 5–6 cópias arquivadas (`fontes/AAAA-MM-DD/<id>.html`).
2. **Envio por e-mail (uma única cópia):** antes de enviar, verificar `outbox/AAAA-MM-DD.sent` e a pasta **Enviados** do Gmail para evitar duplicata. Enviar uma única cópia para `lta2119@columbia.edu` (com `docs/assets/capa-lai.gif` no início e o texto de `outbox/AAAA-MM-DD.txt`), confirmar em Enviados e gravar `outbox/AAAA-MM-DD.sent`. Não acrescentar assinatura manual se a conta já inserir automaticamente.
3. **Linguagem e identidade:** manter a linguagem direta, factual e acessível (não restrita a jornalistas), sem slogans ou marketing, alinhada ao visual Datafixers (`docs/assets/style.css?v=4` e `docs/assets/site.js?v=1`).
