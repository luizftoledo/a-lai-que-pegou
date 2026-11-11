"""Travas de scripts/publish.py. Rodar: python3 -m unittest discover tests"""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import publish  # noqa: E402


def item(headline="Banco lidera novos empréstimos consignados do INSS com 1,6 milhão de operações", pontos=(3, 3, 3, 2, 3), protocol="00000.000001/2026-01"):
    return {
        "headline": headline, "summary": "Resumo.", "why_now": "Agora.", "pitch": "Pista.",
        "source_url": "https://informabr.cgu.gov.br/busca/" + protocol[-4:-3] + protocol[6:12], "protocol": protocol,
        "response_date": "2026-11-05", "attachment_review": "Sem anexo público",
        "evidence": "A resposta lista 1.612.345 operações em 2025 para a instituição, à frente das demais, na tabela mensal entregue.",
        "relevancia": {"pontos": dict(zip(publish.EIXOS, pontos)), "motivos": {e: "Motivo apoiado na resposta." for e in publish.EIXOS},
                       "cobertura": "nao_coberto", "verificado_por": "api"},
    }


def issue(*items):
    return {"date": "2026-11-16", "headline": items[0]["headline"], "deck": "Linha fina.", "items": list(items), "precedents": []}


class Travas(unittest.TestCase):
    def test_edicao_valida(self):
        self.assertEqual(publish.validate(issue(item())), [])

    def test_edicoes_antigas_continuam_validas(self):
        for path in sorted((ROOT / "issues").glob("2026-10-*.json")):
            self.assertEqual(publish.validate(json.loads(path.read_text(encoding="utf-8"))), [], path.name)

    def erros(self, ed):
        return " | ".join(publish.validate(ed))

    def test_item_fraco(self):
        self.assertIn("exige 8", self.erros(issue(item(pontos=(1, 2, 2, 1, 1)))))

    def test_abertura_sem_alcance(self):
        self.assertIn("alcance e clareza", self.erros(issue(item(pontos=(1, 3, 3, 3, 3)))))

    def test_um_item_de_oito_nao_faz_edicao(self):
        self.assertIn("pelo menos dois itens", self.erros(issue(item(pontos=(2, 2, 2, 0, 2)))))

    def test_ordem_por_pontuacao(self):
        fraco, forte = item(pontos=(2, 2, 2, 1, 2)), item("Outro título", protocol="00000.000002/2026-02")
        self.assertIn("maior pontuação", self.erros(issue(fraco, forte)))

    def test_titulo(self):
        self.assertIn("sigla", self.erros(issue(item("MAPA confirma recolhimento de três lotes de vacina"))))
        self.assertIn("máximo 90", self.erros(issue(item("Título " + "muito " * 20 + "longo"))))

    def test_negativa(self):
        neg = item(pontos=(2, 3, 3, 3, 3)); neg["tipo"] = "negativa"
        self.assertIn("negativa só entra", self.erros(issue(neg)))

    def test_bem_coberto_e_resposta_antiga(self):
        x = item(); x["relevancia"]["cobertura"] = "bem_coberto"; x["response_date"] = "2026-09-01"
        e = self.erros(issue(x))
        self.assertIn("bem coberto", e); self.assertIn("21 dias", e)

    def test_protocolo_repetido(self):
        antigo = json.loads((ROOT / "issues" / "2026-10-12.json").read_text(encoding="utf-8"))["items"][0]["protocol"]
        self.assertIn("já publicado", self.erros(issue(item(protocol=antigo))))

    def test_sem_registro(self):
        x = copy.deepcopy(item()); del x["relevancia"]
        self.assertIn("relevancia", self.erros(issue(x)))


if __name__ == "__main__":
    unittest.main()
