#!/usr/bin/env python3
"""Lê pedido e resposta de um protocolo, tentando as fontes em ordem.

Uso: python3 scripts/detalhe.py ID_DO_PEDIDO [--json]

1. API pública do InformaBR (texto integral e lista de anexos).
2. Dados abertos já baixados por scripts/triagem.py (texto até 14 mil caracteres).

Imprime por qual via o texto foi obtido. Esse valor vai no campo
`relevancia.verificado_por` do item da edição: "api" ou "dados_abertos".
A API devolve 403 a partir de alguns provedores de nuvem; nesse caso a segunda
via atende, salvo quando `resposta_cortada` for verdadeiro.
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triagem  # noqa: E402

API = "https://api-laibr.cgu.gov.br/publico/busca/pedidos/{id}"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
      "Accept": "application/json"}


def pela_api(pid):
    with urllib.request.urlopen(urllib.request.Request(API.format(id=pid), headers=UA), timeout=40) as r:
        d = json.loads(r.read().decode("utf-8"))
    return {
        "verificado_por": "api", "id": str(d["idManifestacao"]), "protocolo": d["numProtocoloFormatado"],
        "orgao": d.get("nomeOrgao"), "data_resposta": (d.get("dataResposta") or "")[:10],
        "decisao": d.get("descAvaliacaoManifestacao"), "especificacao": d.get("descClassificacaoAvaliacaoManifestacao"),
        "pedido": d.get("textoManifestacao") or "", "resposta": d.get("resposta") or "", "resposta_cortada": False,
        "anexos": [{"nome": x.get("nomeArquivo"), "id_anexo": x.get("idAnexo"), "tipo": x.get("idTipoAnexo")} for x in d.get("anexos") or []],
        "tem_recurso": bool(d.get("recursos")),
    }


def pelos_dados_abertos(pid):
    for zip_path in sorted(triagem.CACHE.glob("Arquivos_csv_*.zip"), reverse=True):
        for d in triagem.linhas(zip_path, "_Pedidos_csv"):
            if d["IdPedido"] != str(pid):
                continue
            anexos = [{"nome": x["NomeArquivo"], "url": x["UrlArquivo"], "tipo": x["TipoAnexo"]}
                      for x in triagem.linhas(zip_path, "PedidosLinkArquivo") if x["IdPedido"] == str(pid)]
            return {
                "verificado_por": "dados_abertos", "id": d["IdPedido"], "protocolo": triagem.protocolo(d["ProtocoloPedido"]),
                "orgao": d["OrgaoDestinatario"], "data_resposta": triagem.iso(d["DataResposta"]),
                "decisao": d["Decisao"], "especificacao": d["EspecificacaoDecisao"],
                "pedido": (d["ResumoSolicitacao"] + " " + d["DetalhamentoSolicitacao"]).strip(),
                "resposta": d["Resposta"], "resposta_cortada": len(d["Resposta"]) >= triagem.LIMITE_RESPOSTA - 10,
                "anexos": anexos,
            }
    return None


def main():
    pid = sys.argv[1]
    erro_api = None
    try:
        r = pela_api(pid)
    except Exception as e:
        erro_api = f"{type(e).__name__}: {e}"
        r = pelos_dados_abertos(pid)
    if r is None:
        print(f"FALHA: API ({erro_api}) e pedido {pid} ausente dos dados abertos em .cache/. Rode scripts/triagem.py.", file=sys.stderr)
        return 1
    if erro_api:
        r["erro_api"] = erro_api
    if "--json" in sys.argv:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(f"via: {r['verificado_por']}" + (f" (API falhou: {erro_api})" if erro_api else ""))
        print(f"{r['protocolo']} · {r['orgao']} · resposta em {r['data_resposta']} · {r['decisao']} · {r['especificacao']}")
        if r["resposta_cortada"]:
            print("ATENÇÃO: resposta cortada em 14 mil caracteres nos dados abertos; não usar sem ler a íntegra.")
        print("\n--- PEDIDO\n" + r["pedido"] + "\n\n--- RESPOSTA\n" + r["resposta"] + "\n\n--- ANEXOS")
        for x in r["anexos"]:
            print(" ", x)
    return 0


if __name__ == "__main__":
    sys.exit(main())
