"""Two independent host processes cannot overwrite a newer Red Threads collection."""
import concurrent.futures,subprocess,tempfile,json,urllib.request,urllib.error,sys,base64,io,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];results=[];hosts=[]
def call(url,path,data=None,token=None,revision=None):
 headers={}
 if token:headers['X-Work-Token']=token
 if revision:headers['If-Match']=revision
 raw=json.dumps(data).encode() if data is not None else None
 req=urllib.request.Request(url+path,raw,headers)
 try:
  with urllib.request.urlopen(req,timeout=10) as r:return r.status,json.load(r)
 except urllib.error.HTTPError as e:return e.code,json.load(e)
with tempfile.TemporaryDirectory(prefix='red-host-') as home:
 try:
  for _ in range(2):
   proc=subprocess.Popen([sys.executable,str(root/'src/red-threads/workspace/work-host.py'),'--no-browser','--data-home',home],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8');hosts.append(proc)
  urls=[json.loads(p.stdout.readline())['url'] for p in hosts]
  states=[call(u,'api/work')[1] for u in urls]
  data={'schema_version':1,'case':{'id':'a','title':'Inquiry','question':'Who approved what?','updated_at':'2026-10-15T00:00:00Z'},**{k:[] for k in ['sources','nodes','edges','hypotheses','leads','games']}}
  payload={'app':'red-threads','projects':[{'id':'p','data':data}]}
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
   futures=[pool.submit(call,u,'api/work',payload,s['token'],s['revision']) for u,s in zip(urls,states)]
   statuses=sorted(f.result()[0] for f in futures)
  assert statuses==[200,409],statuses;results.append('two independent processes: one accepted same-base write, one conflict')
  stored=(Path(home)/'work.json').read_bytes();state=call(urls[0],'api/work')[1]
  malformed={'app':'red-threads','projects':[{'id':'bad','data':{}}]};assert call(urls[0],'api/work',malformed,state['token'],state['revision'])[0]==400;assert (Path(home)/'work.json').read_bytes()==stored;results.append('invalid native case leaves saved bytes unchanged')
  document=io.BytesIO()
  with zipfile.ZipFile(document,'w') as z:z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>A real supplied agreement passage.</w:t></w:r></w:p></w:body></w:document>')
  status,res=call(urls[0],'api/read-docx',{'data':base64.b64encode(document.getvalue()).decode()},state['token'])
  assert status==200 and res['text']=='A real supplied agreement passage.';results.append('ordinary DOCX text read locally without altering the saved case')
  assert call(urls[0],'api/read-docx',{'data':base64.b64encode(b'not a zip').decode()},state['token'])[0]==400;results.append('malformed DOCX produces recoverable error')
  evidence=root/'verification/purpose-rebuild/HOST-ACCEPTANCE.json';evidence.write_text(json.dumps({'status':'PASS','checks':results},indent=2),encoding='utf-8');print(evidence.read_text(encoding='utf-8'))
 finally:
  for p in hosts:p.terminate();p.wait(timeout=10)
