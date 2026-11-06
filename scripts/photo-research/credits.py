import json,html,re
from pathlib import Path
root=Path(__file__).resolve().parents[2]
photos=json.loads((root/'frontend/app/food-photos.json').read_text())
e=html.escape
rows=[]
for name,p in photos.items():
 slug=re.sub('[^a-z0-9]+','-',name).strip('-')
 rows.append(f'<article id="{slug}"><img src="{e(p["src"])}" alt="{e(name)}" loading="lazy"><div><h2>{e(name.title())}</h2><p><a href="{e(p["source"])}">{e(p["title"])}</a> by {e(p["author"])}</p><p><a href="{e(p["licenseUrl"])}">{e(p["license"])}</a> · Wikimedia Commons</p><p>{e(p["changes"])}</p></div></article>')
(root/'frontend/public/photo-credits.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Food photo credits · DumHouse</title><style>body{font:16px/1.6 system-ui;background:#fffaf3;color:#30251e;max-width:960px;margin:auto;padding:32px}a{color:#a6380b}article{display:flex;gap:24px;padding:24px 0;border-bottom:1px solid #e8dacf}img{width:150px;height:130px;object-fit:cover;border-radius:12px}h2{margin:0;font-size:22px}p{margin:8px 0}@media(max-width:600px){article{display:block}img{width:100%;height:220px}}</style><a href="/menu">← Back to menu</a><h1>Food photo credits</h1><p>Real food photographs from independent contributors. These are representative dishes, not photographs from the DumHouse kitchen. Recipes, portions and presentation may vary. Adapted versions retain the source license shown below. Photo rights remain with their respective creators under the licenses below.</p>'''+''.join(rows)+'</html>')
