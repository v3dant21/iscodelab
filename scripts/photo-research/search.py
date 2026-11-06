import requests,json,time,concurrent.futures
from pathlib import Path
queries='''chicken biryani|mutton biryani|paneer biryani|chicken 65|mirchi ka salan|double ka meetha|vegetable biryani|mushroom biryani|kaju biryani|egg biryani|prawn biryani|lassi|chaas|gulab jamun|khubani ka meetha|tandoori chicken|tangdi kebab|reshmi kebab|chicken tikka|achari chicken|lamb chops|seekh kebab|fish tikka|chapati|tandoori roti|naan|butter naan|garlic naan|lachha paratha|paneer kulcha|tomato soup|coriander soup|gobi 65|vegetable manchurian|paneer 65|chilli paneer|chilli baby corn|apollo fish|prawn fry|malai kofta|paneer butter masala|palak paneer|kadai paneer|mushroom curry|dal fry|andhra chicken|kadai chicken|butter chicken|gongura chicken|mutton curry|gongura mutton|jeera rice|vegetable fried rice|curd rice|egg fried rice|chicken fried rice|egg curry|indian omelette'''.split('|')
out=Path('/tmp/food-search');out.mkdir(exist_ok=True)
def run(q):
 p=out/(q+'.json')
 if p.exists():return
 time.sleep(8)
 try:
  r=requests.get('https://commons.wikimedia.org/w/api.php',headers={'User-Agent':'DumHouseMenuPhotoResearch/1.0 (local demo photo attribution research)'},params={'action':'query','format':'json','generator':'search','gsrsearch':q+' filetype:bitmap','gsrnamespace':6,'gsrlimit':8,'prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':800},timeout=40)

  if r.status_code == 429:
   time.sleep(60)
   return run(q)
  r.raise_for_status();p.write_text(json.dumps(r.json()))
 except Exception as e: print(q,str(e),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:list(ex.map(run,queries))
for q in queries:
 p=out/(q+'.json')
 if p.exists():
  pages=sorted(json.loads(p.read_text()).get('query',{}).get('pages',{}).values(),key=lambda x:x.get('index',0))
  print(q+': '+ ' | '.join(str(i)+' '+x['title'] for i,x in enumerate(pages)))
