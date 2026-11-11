# Critérios de seleção — A LAI que pegou

Vale para edições a partir de 11/11/2026. As travas estão em `scripts/publish.py`.

## 1. Para quem

O leitor é um repórter que não cobre o órgão nem o tema do pedido. Ele precisa
entender, pelo título, que fato a resposta revela e por que isso atinge muita
gente.

Teste antes de pontuar: explicar o achado em duas frases a alguém fora da área.
Se a pessoa perguntaria "e daí?", o pedido não entra.

Resposta inédita não é critério. Um assunto pequeno que ninguém cobriu continua
pequeno.

## 2. Pontuação

Cinco eixos, de 0 a 3, cada um com motivo escrito apoiado na resposta. Máximo 15.

| Eixo | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| **Alcance** | um órgão, um hospital, uma carreira pequena | uma categoria, uma cidade pequena, um setor | centenas de milhares de pessoas, ou um estado ou capital num serviço | milhões de pessoas, ou todos os usuários de um serviço essencial |
| **Efeito** | curiosidade ou rotina administrativa | procedimento interno do governo | direito, obrigação, serviço ou gasto público grande | dinheiro, saúde, segurança, escola, moradia ou liberdade das pessoas |
| **Solidez** | negativa ou resposta genérica | o órgão admite que não tem ou não controla o dado | confirmação oficial de fato concreto | dado ou documento entregue, com números ou anexo lido |
| **Atualidade** | sem gancho | tema recorrente, sem data | decisão, prazo ou debate nos próximos 30 dias | assunto no noticiário desta semana |
| **Clareza** | só especialista entende | exige explicar um mecanismo | explicável com um exemplo | cabe em uma frase sem sigla |

## 3. Destino

| Total | Destino |
|---|---|
| 11 ou mais, com alcance e clareza de pelo menos 2 | Pode abrir a edição |
| 8 a 10 | Item (`items`) |
| 5 a 7 | Uma linha em "Também responderam" (`tambem_responderam`) |
| menos de 5 | Fora |

- O primeiro item é o de maior pontuação.
- Sem nenhum pedido com 8 pontos, não há edição: registrar a rodada com
  `scripts/rodada_sem_edicao.py`.
- Sem pedido com 11 pontos, a edição sai sem abertura forte só se houver pelo
  menos dois itens com 8 ou mais; o primeiro precisa ter alcance e clareza de
  pelo menos 2.
- Até seis itens.

## 4. Negativas

Negativa tem solidez 0. Só entra com alcance 3 e efeito 3, marcada com
`"tipo": "negativa"`. Nunca completa edição.

## 5. Relação com o noticiário

Registrar em `relevancia.cobertura`:

- `nao_coberto`: nenhum veículo publicou o fato.
- `coberto_sem_o_dado`: o assunto saiu, sem o número ou o documento que a
  resposta traz. Entra, com o dado no título.
- `bem_coberto`: já publicado com o mesmo dado. Fica fora.

## 6. Título e texto

- Título com até 90 caracteres, sujeito concreto e verbo no presente, dizendo o
  fato e não o trâmite.
- Sem sigla fora do uso corrente no título. Liberadas: as de `SIGLAS_LIVRES` em
  `scripts/publish.py` (INSS, SUS, CPF, EUA, STF e semelhantes). As demais por
  extenso ou pelo nome comum: "Ministério da Agricultura", não "MAPA".
- No máximo dois números no título.
- Resumo: o que a resposta revela, para quem importa, qual número sustenta.
  Valores com comparação (por pessoa, por mês, em relação ao ano anterior).
- Sem adjetivo de avaliação nem frase de efeito.

## 7. Verificação

- Texto lido pela API do InformaBR (`verificado_por: api`) ou pelos dados
  abertos (`verificado_por: dados_abertos`). Use `scripts/detalhe.py ID`.
- Resposta cortada em 14 mil caracteres nos dados abertos só entra depois de
  lida pela API ou pela página.
- Anexo inacessível não derruba o item quando todos os fatos publicados estão
  no texto da resposta. Registrar isso em `attachment_review` e não usar nada do
  anexo.
- Resposta com data de até 21 dias antes da edição.
- Protocolo já publicado em edição anterior não volta.

## 8. Precedentes

Sem mudança: só decisão de CGU ou CMRI que reverteu negativa ou levou à entrega
de informação concreta de interesse público. A seção vem no fim e não dá o
título. `data/candidatos.json` lista em `recursos` as decisões deferidas ou com
perda de objeto; a leitura da decisão integral continua obrigatória.

## 9. Registro por item

```json
"relevancia": {
  "pontos":  {"alcance": 3, "efeito": 3, "solidez": 3, "atualidade": 2, "clareza": 3},
  "motivos": {"alcance": "...", "efeito": "...", "solidez": "...", "atualidade": "...", "clareza": "..."},
  "cobertura": "nao_coberto",
  "verificado_por": "api"
}
```

A pontuação fica no JSON da edição e não aparece na página.
