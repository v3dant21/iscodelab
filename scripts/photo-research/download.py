"""Download explicitly selected Wikimedia photos, preserving source and license credits."""
import json,re,html,time,requests,hashlib
from pathlib import Path
from PIL import Image
from io import BytesIO
root=Path(__file__).resolve().parents[2]
selection=json.loads((Path(__file__).parent/'selection.json').read_text())
out=root/'frontend/public/images/dishes';out.mkdir(exist_ok=True)
manifest=json.loads((root/'frontend/app/food-photos.json').read_text()) if (root/'frontend/app/food-photos.json').exists() else {}
for name,(query,index) in selection.items():
 pages=sorted(json.loads((Path('/tmp/food-search')/(query+'.json')).read_text())['query']['pages'].values(),key=lambda x:x.get('index',0))
 page=pages[index];info=page['imageinfo'][0];meta=info['extmetadata']
 def val(k):return html.unescape(re.sub('<[^>]*>','',meta.get(k,{}).get('value',''))).strip()
 license=val('LicenseShortName')
 assert license.startswith(('CC BY','CC0','Public domain')), (name,license)
 slug=re.sub('[^a-z0-9]+','-',name).strip('-');dest=out/(slug+'.webp')
 if dest.exists() and name in manifest and manifest[name]['source'] != info['descriptionurl']:
  dest.unlink()
 if not dest.exists():
  url=info.get('thumburl',info['url'])
  r=requests.get(url,headers={'User-Agent':'DumHouseMenuPhotoResearch/1.0 (local demo)'},timeout=15)
  if r.status_code==429:
   time.sleep(8)
   r=requests.get(url,headers={'User-Agent':'DumHouseMenuPhotoResearch/1.0 (local demo)'},timeout=15)
  if r.status_code!=200:print(name,r.status_code,flush=True);continue
  im=Image.open(BytesIO(r.content));im.thumbnail((1000,1000));im.convert('RGB').save(dest,'WEBP',quality=85)
  time.sleep(1)
 manifest[name]={'src':'/images/dishes/'+dest.name,'title':page['title'][5:],'source':info['descriptionurl'],'author':val('Artist'),'license':license,'licenseUrl':val('LicenseUrl'),'description':val('ImageDescription'),'changes':'Resized, converted to WebP; cropped to fit in the menu.'}
 (root/'frontend/app/food-photos.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
 print(name,'OK',flush=True)
(root/'frontend/app/food-photos.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
