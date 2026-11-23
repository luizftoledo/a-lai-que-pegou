import json, html, re, textwrap, zipfile
from pathlib import Path
from PIL import Image,ImageFont,ImageOps,ImageDraw
import cairosvg
root=Path(__file__).resolve().parents[1];issue=json.loads((root/'issues/2026-11-23.json').read_text());out=root/'cards-2026-11-23';out.mkdir(exist_ok=True)
INK='#123c32';MINT='#b9e5cc';PAPER='#f6f3e8';GRAY='#486158'
fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
logo=(root/'docs/assets/datafixers_logo.svg').read_text();logo=logo[logo.index('<svg'):];logo=logo.replace('<svg ','<svg x="700" y="1220" width="310" height="68" ',1)
font=lambda n:ImageFont.truetype(fontfile,n)
def wrap(s,n=38,width=900):
 f=font(n);lines=[]
 for para in s.split('\n'):
  line=''
  for word in para.split():
   test=(line+' '+word).strip()
   if f.getlength(test)>width and line: lines.append(line);line=word
   else:line=test
  if line:lines.append(line)
  lines.append('')
 return lines[:-1]
def txt(s,x,y,n=38,width=900,lh=None,center=False,highlight=False):
 ls=wrap(s,n,width);lh=lh or n*1.4;pieces=[]
 for j,l in enumerate(ls):
  if not l:continue
  yy=y+j*lh;xx=540 if center else x;w=font(n).getlength(l)
  if highlight and j%2==0:pieces.append(f'<rect x="{xx-w/2-9 if center else xx-7}" y="{yy-n+2}" width="{w+18}" height="{n+12}" fill="{MINT}"/>')
  pieces.append(f'<text x="{xx}" y="{yy}" font-size="{n}" text-anchor="{"middle" if center else "start"}">{html.escape(l)}</text>')
 return ''.join(pieces),y+len(ls)*lh

def footer():return f'<line x1="72" y1="1200" x2="1008" y2="1200" stroke="{INK}" opacity=".2"/><text x="475" y="1260" font-size="24">A LAI que pegou</text>'+logo

def illus(y=230):
 return f'''<g transform="translate(260 {y})" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"><circle cx="95" cy="70" r="38" fill="{MINT}"/><path d="M40 190 Q40 112 95 112 Q145 112 175 195"/><path d="M98 185 L198 225"/><rect x="195" y="125" width="230" height="145" rx="10" fill="{PAPER}"/><path d="M172 271 L448 271 L470 288 L150 288 Z" fill="{MINT}"/><circle cx="357" cy="97" r="62" fill="{MINT}" fill-opacity=".6"/><path d="M401 141 L462 202" stroke-width="17"/></g>'''

def save(group,num,body):
 p=out/group;p.mkdir(exist_ok=True);svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350" viewBox="0 0 1080 1350"><rect width="1080" height="1350" fill="{PAPER}"/><g font-family="DejaVu Sans" font-weight="400" fill="{INK}">'+body+footer()+'</g></svg>'
 (p/f'{num:02}.svg').write_text(svg);cairosvg.svg2png(bytestring=svg.encode(),write_to=str(p/f'{num:02}.png'))

def title(s,y=380,n=58):
 ls=wrap(s,n,900);b,yy=txt(s,90,y,n,900,n*1.33,True,True);assert yy<1170,(s,yy);return b
b='<text x="72" y="105" font-size="24" letter-spacing="4">SITE · 23 NOV 2026</text>'
titleparts=['A','LAI','que pegou'];tx=540-(sum(font(62).getlength(t) for t in titleparts)+40)/2
for k,t in enumerate(titleparts):
 b+=f'<text x="{tx}" y="345" font-size="62" fill="{INK if k!=1 else "#176248"}">{html.escape(t)}</text>';tx+=font(62).getlength(t)+20
a,_=txt('O que respostas enviadas por meio da Lei de Acesso à Informação revelam',100,445,36,840,52,True);b+=a+illus(640)
save('01-apresentacao',1,b)
b='<text x="72" y="110" font-size="24" letter-spacing="3">COMO FUNCIONA</text>'
a,y=txt('Um garimpo semanal de respostas oficiais',72,235,54,900,70,False,True);b+=a
a,y=txt('Projeto experimental de triagem de pedidos de informação de interesse público com apoio de IA.\n\nToda semana, selecionamos respostas e examinamos precedentes que podem ajudar novos pedidos.\n\nTodas as fontes são oficiais e estão elencadas no site, com os números dos protocolos para checagem na origem.',72,y+55,37,900,54);b+=a
assert y<1170;save('01-apresentacao',2,b)
b='<text x="72" y="110" font-size="24" letter-spacing="3">NESTA EDIÇÃO · 23/11/2026</text>'
a,y=txt('Cinco achados para conferir',72,235,52,900,70,False,True);b+=a
short=['Bets: 37.360 domínios enviados para bloqueio em outubro','Angra: só uma de seis estações geotécnicas operacional','Seguro-defeso: R$ 5,97 bilhões em pagamentos','Roraima: ministério não registra adesão ao fluxo pós-resgate','Mercosul–União Europeia: o que a projeção pressupõe']
for j,s in enumerate(short):
 a,y=txt(s,110,y+35,33,850,45);b+=f'<circle cx="80" cy="{y-len(wrap(s,33,850))*45-12}" r="6" fill="{INK}"/>'+a
b+='<rect x="72" y="1072" width="400" height="66" rx="4" fill="'+MINT+'"/><text x="92" y="1117" font-size="34">LINK NA BIO</text>';save('01-apresentacao',3,b)
orgs=['Ministério da Fazenda','Ministério da Ciência, Tecnologia e Inovação / Cemaden','Ministério do Trabalho e Emprego','Ministério dos Direitos Humanos e da Cidadania','Ministério do Desenvolvimento, Indústria, Comércio e Serviços']
for j,(i,org) in enumerate(zip(issue['items'],orgs),2):
 g=f'{j:02}-'+['bets','cemaden','seguro-defeso','roraima','mercosul'][j-2]
 b='<text x="540" y="110" text-anchor="middle" font-size="24" letter-spacing="3">O QUE A RESPOSTA REVELA</text>'+title(i['headline'],380,56)
 save(g,1,b)
 b='<text x="72" y="110" font-size="24" letter-spacing="3">O DADO E SEUS LIMITES</text>'
 a,y=txt(i['summary'],72,235,36,930,50,False,False);b+=a
 if y>1160:raise ValueError((g,y))
 # Highlight retângulo no subtítulo, mantendo tipografia regular no corpo.
 b+='<rect x="72" y="145" width="350" height="45" fill="'+MINT+'"/><text x="83" y="178" font-size="26">Fonte oficial · LAI</text>'
 save(g,2,b)
 b='<text x="72" y="110" font-size="24" letter-spacing="3">CONFIRA NA FONTE</text>'+illus(180)
 a,y=txt('Dados oficiais de '+org+'.\n\nResposta obtida pela Lei de Acesso à Informação, em '+i['response_date'][8:]+'/'+i['response_date'][5:7]+'/'+i['response_date'][:4]+'.',72,620,34,930,48);b+=a
 a,y=txt('Pedido, resposta completa e protocolo para copiar estão no site.',72,y+28,32,930,46);b+=a
 b+='<rect x="72" y="1015" width="400" height="66" fill="'+MINT+'"/><text x="92" y="1060" font-size="34">LINK NA BIO</text><text x="72" y="1138" font-size="29">datafixers.org/a-lai-que-pegou</text>'
 save(g,3,b)
# Arquivo de legendas e fontes copiáveis, sem protocolos nas imagens.
capt=[]
for j,i in enumerate(issue['items'],2):capt.append(f'{j:02}\n{i["headline"]}\n\n{i["summary"]}\n\nProtocolo: {i["protocol"]}\nFonte: {i["transcript_url"]}\nLeia no link da bio.\n')
(out/'legendas.txt').write_text('01 · Apresentação\nA LAI que pegou é um projeto experimental de triagem de pedidos de informação de interesse público com apoio de IA. Fontes oficiais e protocolos para checagem no site. Edição de 23/11/2026. Leia no link da bio.\n\n'+'\n\n'.join(capt))
thumbs=[]
for p in sorted(out.glob('*/*.png')):
 im=Image.open(p).resize((270,338));thumbs.append((p,im))
canvas=Image.new('RGB',(810,6*370),'#ddd')
draw=ImageDraw.Draw(canvas)
for n,(p,im) in enumerate(thumbs):x0=(n%3)*270;y0=(n//3)*370;canvas.paste(im,(x0,y0));draw.text((x0+4,y0+340),p.parent.name+' '+p.stem,fill='black')
canvas.save(out/'revisao.jpg')
with zipfile.ZipFile(root/'a-lai-que-pegou-carrosseis-2026-11-23.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(out.rglob('*')):
  if p.is_file() and p.name!='revisao.jpg':z.write(p,p.relative_to(out))
print('18 cards PNG 1080x1350, fontes SVG editáveis e legendas gerados.')
