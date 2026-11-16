#!/usr/bin/env python3
"""Arquiva os textos públicos usados na edição, sem depender do portal de busca.

Uso: python3 scripts/arquivar_fontes.py issues/AAAA-MM-DD.json .cache/Arquivos_csv_2026.zip
Mantém texto e metadados de origem em JSON; HTML identifica expressamente a cópia.
Não inclui dados de solicitantes nem afirma ter arquivado anexos.
"""
import hashlib
import html
import json
import re
import sys
import zipfile
from pathlib import Path

import triagem

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://luizftoledo.github.io/a-lai-que-pegou/"


def main():
    issue_path, zip_path = map(Path, sys.argv[1:3])
    issue = json.loads(issue_path.read_text())
    ids = {x['source_url'].rsplit('/', 1)[-1] for x in issue['items']}
    rows = {d['IdPedido']: d for d in triagem.linhas(zip_path, '_Pedidos_csv') if d['IdPedido'] in ids}
    if set(rows) != ids:
        raise ValueError('Pedido ausente da base: ' + str(ids - set(rows)))
    attachments = {pid: [] for pid in ids}
    for d in triagem.linhas(zip_path, 'PedidosLinkArquivo'):
        if d['IdPedido'] in ids:
            attachments[d['IdPedido']].append({k: d[k] for k in ('NomeArquivo', 'TipoAnexo', 'UrlArquivo')})
    with zipfile.ZipFile(zip_path) as z:
        csv_name = next(n for n in z.namelist() if '_Pedidos_csv' in n)
    digest = hashlib.file_digest(zip_path.open('rb'), 'sha256').hexdigest()
    out = ROOT / 'docs' / 'fontes' / issue['date']
    out.mkdir(parents=True, exist_ok=True)
    for item in issue['items']:
        pid = item['source_url'].rsplit('/', 1)[-1]
        d = rows[pid]
        if len(d['Resposta']) >= triagem.LIMITE_RESPOSTA - 10:
            raise ValueError('Resposta possivelmente cortada: ' + pid)
        record = {
            'id_pedido': pid, 'protocolo': triagem.protocolo(d['ProtocoloPedido']),
            'orgao': d['OrgaoDestinatario'], 'data_registro': triagem.iso(d['DataRegistro']),
            'data_resposta': triagem.iso(d['DataResposta']), 'decisao': d['Decisao'],
            'resumo_solicitacao': d['ResumoSolicitacao'], 'pedido': d['DetalhamentoSolicitacao'],
            'resposta': d['Resposta'], 'resposta_cortada': False,
            'anexos_informados_pela_cgu': attachments[pid],
            'proveniencia': {'editor': 'A LAI que pegou', 'tipo': 'Cópia de textos da base pública da CGU; não é uma página da CGU.',
                            'registro_oficial': item['source_url'], 'zip_oficial': item['open_data_url'],
                            'arquivo_csv': csv_name, 'zip_sha256': digest,
                            'edicao': issue['date'], 'anexos': 'A lista abaixo não significa que os arquivos foram abertos ou arquivados.'},
        }
        raw = json.dumps(record, ensure_ascii=False, indent=2) + '\n'
        (out / f'{pid}.json').write_text(raw, encoding='utf-8')
        e = html.escape
        def text(t):
            return e(re.sub(r'[\x00-\x08\x0b-\x1f]', '', t))
        att = ''.join(f'<li>{e(a["TipoAnexo"])}: <a href="{e(a["UrlArquivo"], quote=True)}">{e(a["NomeArquivo"])}</a></li>' for a in attachments[pid])
        page = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pedido {e(record['protocolo'])} · Texto da base CGU</title>
<style>body{{font:17px/1.7 Inter,system-ui,sans-serif;max-width:900px;margin:40px auto;padding:0 20px;color:#141312;background:#fbfbfa}}a{{color:#2a7975;overflow-wrap:anywhere}}pre{{white-space:pre-wrap;font:inherit;overflow-wrap:anywhere}}.notice{{background:#eff4f3;padding:18px;border-left:3px solid #2a7975}}h1{{font:300 32px/1.15 Fraunces,Georgia,serif;letter-spacing:-.02em}}code{{overflow-wrap:anywhere}}</style></head><body>
<a href="../../edicoes/{issue['date']}.html">← Voltar à edição</a><h1>Pedido e resposta: {e(record['protocolo'])}</h1>
<p class="notice"><strong>Cópia dos dados abertos da CGU.</strong> Esta página é mantida por A LAI que pegou e não é uma página governamental. Reproduz os campos públicos de pedido e resposta, sem resumo editorial. Apenas caracteres de controle de formatação foram removidos da exibição; o JSON conserva os campos extraídos. Anexos não estão incorporados.</p>
<p><strong>Órgão:</strong> {e(record['orgao'])}<br><strong>Pedido:</strong> {e(record['data_registro'])}<br><strong>Resposta:</strong> {e(record['data_resposta'])}<br><strong>Decisão registrada:</strong> {e(record['decisao'])}</p>
<p><a href="{e(item['source_url'])}">Registro original no InformaBR</a> · <a href="{pid}.json" download>Baixar os textos e a origem (JSON)</a> · <a href="{e(item['open_data_url'])}">Baixar base oficial da CGU (ZIP)</a></p>
<h2>Pedido</h2><pre>{text(record['pedido'])}</pre><h2>Resposta</h2><pre>{text(record['resposta'])}</pre>
<h2>Anexos listados na base</h2><p>Links fornecidos pela CGU, sujeitos à disponibilidade do portal. A lista não indica revisão nem cópia dos anexos.</p><ul>{att or '<li>Sem anexo público listado.</li>'}</ul>
<h2>Origem e conferência</h2><p>Arquivo: <code>{e(csv_name)}</code>. SHA-256 do ZIP utilizado: <code>{digest}</code>. SHA-256 deste JSON: <code>{hashlib.sha256(raw.encode()).hexdigest()}</code>.</p>
<p>O campo de resposta tem {len(record['resposta'])} caracteres e não atingiu o limite de corte da base. A leitura não inclui documentos de anexos nem todo o histórico de recursos.</p></body></html>'''
        (out / f'{pid}.html').write_text(page, encoding='utf-8')
        item['transcript_url'] = BASE + f"fontes/{issue['date']}/{pid}.html"
    issue_path.write_text(json.dumps(issue, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(ids)} pedidos e respostas arquivados, sem anexos.')


if __name__ == '__main__':
    main()
