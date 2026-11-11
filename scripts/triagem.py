#!/usr/bin/env python3
"""Triagem semanal a partir dos dados abertos de pedidos de LAI (CGU).

Uso: python3 scripts/triagem.py [--dias 10] [--max 150] [--dias-recursos 45]

Baixa o ZIP anual publicado pela CGU, separa os pedidos respondidos na janela
e grava data/candidatos.json. Não usa a API do InformaBR nem navegador, então
roda em qualquer máquina, inclusive GitHub Actions.

A pontuação gravada aqui (`pontos_triagem`) é mecânica e serve só para ordenar
a leitura. A pontuação editorial é a de CRITERIOS.md, dada por quem leu a
resposta.

Saída: 0 = candidatos gravados; 2 = fonte desatualizada (candidatos gravados
mesmo assim, com aviso); 1 = falha de download ou de leitura.
"""
import argparse
import csv
import io
import json
import re
import sys
import urllib.error
import urllib.request
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache"
OUT = ROOT / "data" / "candidatos.json"
BASE = "https://dadosabertos-download.cgu.gov.br/FalaBR/Arquivos_FalaBR_Filtrado/Arquivos_csv_{ano}.zip"
UA = {"User-Agent": "Mozilla/5.0"}
LIMITE_RESPOSTA = 14000  # a CGU corta o campo Resposta nesse tamanho
FONTE_VELHA_DIAS = 3

DESCARTAR_DECISAO = {
    "Não se trata de solicitação de informação",
    "Órgão não tem competência para responder sobre o assunto",
    "Pergunta Duplicada/Repetida",
}
RECURSO_FAVORAVEL = {"Deferido", "Parcialmente deferido", "Perda de objeto", "Perda de objeto parcial"}
NEGATIVAS = {"Acesso Negado", "Informação Inexistente"}
PESSOAL = re.compile(
    r"\b(meu|minha|meus|minhas)\s+(cpf|benef[ií]cio|aposentadoria|processo|pedido|requerimento|"
    r"cadastro|aux[ií]lio|nome|dados|d[ií]vidas?|passaporte|diploma|matr[ií]cula|inscri[cç][aã]o|"
    r"sal[aá]rio|contracheque|prontu[aá]rio|pens[aã]o|visto|recurso|nota|prova)\b",
    re.I,
)
NUMERO = re.compile(r"R\$\s?[\d.]+(?:,\d+)?|\b\d{1,3}(?:\.\d{3})+(?:,\d+)?\b|\b\d+(?:,\d+)?\s?%")


def baixar(ano):
    """Baixa o ZIP do ano se o servidor tiver versão mais nova que a do cache."""
    CACHE.mkdir(exist_ok=True)
    destino = CACHE / f"Arquivos_csv_{ano}.zip"
    meta = CACHE / f"Arquivos_csv_{ano}.json"
    headers = dict(UA)
    if destino.exists() and meta.exists():
        headers["If-Modified-Since"] = json.loads(meta.read_text())["last_modified"]
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE.format(ano=ano), headers=headers), timeout=300) as r:
            destino.write_bytes(r.read())
            meta.write_text(json.dumps({"last_modified": r.headers.get("Last-Modified", "")}))
    except urllib.error.HTTPError as e:
        if e.code != 304:
            raise
    return destino, json.loads(meta.read_text())["last_modified"]


def linhas(zip_path, trecho):
    with zipfile.ZipFile(zip_path) as z:
        nome = next(n for n in z.namelist() if trecho in n)
        texto = io.TextIOWrapper(z.open(nome), encoding="utf-16", newline="")
        leitor = csv.reader((l.replace("\0", "") for l in texto), delimiter=";", quoting=csv.QUOTE_NONE)
        cab = next(leitor)
        for linha in leitor:
            if len(linha) == len(cab):
                yield dict(zip(cab, (c.strip() for c in linha)))


def iso(br):
    m = re.match(r"(\d\d)/(\d\d)/(\d{4})", br or "")
    return f"{m[3]}-{m[2]}-{m[1]}" if m else ""


def protocolo(p):
    return f"{p[:5]}.{p[5:11]}/{p[11:15]}-{p[15:]}" if len(p) == 17 and p.isdigit() else p


def ja_publicados():
    vistos = set()
    for arq in (ROOT / "issues").glob("*.json"):
        ed = json.loads(arq.read_text(encoding="utf-8"))
        for bloco in ("items", "precedents", "tambem_responderam"):
            vistos.update(x.get("protocol", "") for x in ed.get(bloco, []))
    return vistos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=10)
    ap.add_argument("--max", type=int, default=150)
    ap.add_argument("--dias-recursos", type=int, default=45)
    ap.add_argument("--hoje", default=date.today().isoformat(), help="AAAA-MM-DD, para reprocessar uma data")
    a = ap.parse_args()
    hoje = date.fromisoformat(a.hoje)
    inicio = (hoje - timedelta(days=a.dias)).isoformat()
    inicio_rec = (hoje - timedelta(days=a.dias_recursos)).isoformat()
    anos = sorted({hoje.year, (hoje - timedelta(days=a.dias_recursos)).year})

    try:
        fontes = [baixar(ano) for ano in anos]
    except Exception as e:  # rede, 403, arquivo ausente
        print(f"FALHA: download dos dados abertos: {e}", file=sys.stderr)
        return 1

    publicados = ja_publicados()
    candidatos, recursos, ids = [], [], set()
    total_janela, mais_recente = 0, ""
    for zip_path, _ in fontes:
        for d in linhas(zip_path, "_Pedidos_csv"):
            resp_em = iso(d["DataResposta"])
            mais_recente = max(mais_recente, resp_em)
            if not (inicio <= resp_em <= hoje.isoformat()):
                continue
            total_janela += 1
            prot = protocolo(d["ProtocoloPedido"])
            pedido = (d["ResumoSolicitacao"] + " " + d["DetalhamentoSolicitacao"]).strip()
            if d["Decisao"] in DESCARTAR_DECISAO or prot in publicados or PESSOAL.search(pedido):
                continue
            resposta = d["Resposta"]
            numeros = len(NUMERO.findall(resposta))
            negativa = d["Decisao"] in NEGATIVAS
            pontos = min(3, numeros // 4) + (2 if "R$" in resposta else 0) + (1 if len(resposta) > 2000 else 0) \
                + (0 if negativa else 2) - (2 if d["EspecificacaoDecisao"].startswith("Orientação sobre como encontrar") else 0)
            candidatos.append({
                "id": d["IdPedido"], "protocolo": prot, "orgao": d["OrgaoDestinatario"],
                "url": f"https://informabr.cgu.gov.br/busca/{d['IdPedido']}",
                "data_registro": iso(d["DataRegistro"]), "data_resposta": resp_em,
                "decisao": d["Decisao"], "especificacao": d["EspecificacaoDecisao"],
                "motivo_negativa": d["MotivoNegativaAcesso"], "negativa": negativa,
                "assunto": d["AssuntoPedido"], "pedido": pedido[:2500],
                "resposta": resposta, "resposta_cortada": len(resposta) >= LIMITE_RESPOSTA - 10,
                "anexos_resposta": [], "numeros_na_resposta": numeros, "pontos_triagem": pontos,
            })
        por_id = {c["id"]: c for c in candidatos}
        for d in linhas(zip_path, "PedidosLinkArquivo"):
            c = por_id.get(d["IdPedido"])
            if c and d["TipoAnexo"] == "Anexo Resposta":
                c["anexos_resposta"].append({"nome": d["NomeArquivo"], "url": d["UrlArquivo"]})
        for d in linhas(zip_path, "_Recursos_csv"):
            dec_em = iso(d["DataResposta"])
            if d["Instancia"] not in ("CGU", "CMRI") or not (inicio_rec <= dec_em <= hoje.isoformat()):
                continue
            # Em CGU/CMRI o campo InformacaoConcedida vem sempre negativo; o resultado está em TipoResposta.
            # "Perda de objeto" costuma indicar entrega durante o recurso: conferir na decisão.
            if d["TipoResposta"] not in RECURSO_FAVORAVEL or d["IdRecurso"] in ids:
                continue
            prot = protocolo(d["ProtocoloPedido"])
            if prot in publicados:
                continue
            ids.add(d["IdRecurso"])
            recursos.append({
                "id_recurso": d["IdRecurso"], "id_pedido": d["IdPedido"], "protocolo": prot,
                "orgao": d["OrgaoDestinatario"] or d["OrgaoPedido"], "instancia": d["Instancia"],
                "url": f"https://informabr.cgu.gov.br/busca/{d['IdPedido']}",
                "data_decisao": dec_em, "tipo_resposta": d["TipoResposta"],
                "informacao_concedida": d["InformacaoConcedida"],
                "recurso": d["DescRecurso"][:2500], "decisao": d["RespostaRecurso"],
            })

    # Resposta curta sem anexo quase nunca traz dado; fica fora da leitura.
    candidatos = [c for c in candidatos if len(c["resposta"]) >= 500 or c["anexos_resposta"]]
    for c in candidatos:
        c["pontos_triagem"] += 2 if c["anexos_resposta"] else 0
    candidatos.sort(key=lambda c: (-c["pontos_triagem"], -len(c["resposta"])))
    recursos.sort(key=lambda r: r["data_decisao"], reverse=True)

    atraso = (hoje - date.fromisoformat(mais_recente)).days if mais_recente else 999
    velha = atraso > FONTE_VELHA_DIAS
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fonte": {"urls": [BASE.format(ano=x) for x in anos], "last_modified": [lm for _, lm in fontes],
                  "resposta_mais_recente": mais_recente, "dias_de_atraso": atraso, "desatualizada": velha},
        "janela": {"de": inicio, "ate": hoje.isoformat(), "recursos_de": inicio_rec},
        "respondidos_na_janela": total_janela, "apos_filtros": len(candidatos),
        "candidatos": candidatos[:a.max], "recursos": recursos,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{total_janela} respondidos de {inicio} a {hoje}; {len(candidatos)} após filtros; "
          f"{min(len(candidatos), a.max)} gravados; {len(recursos)} recursos deferidos ou com perda de objeto (CGU/CMRI). "
          f"Resposta mais recente na base: {mais_recente}.")
    if velha:
        print(f"AVISO: a base está {atraso} dias atrás de {hoje}.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
