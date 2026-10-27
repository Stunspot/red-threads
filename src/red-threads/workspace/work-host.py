"""Local product workspace with persistent private work, independent of browser ports."""
import argparse,json,os,secrets,sys,tempfile,threading,webbrowser,hashlib
from contextlib import contextmanager
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlsplit,unquote,parse_qs
import base64,io,zipfile,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import red_threads,render_atlas
ROOT=Path(__file__).resolve().parent
PRODUCT="red-threads"
MAX=40*1024*1024
@contextmanager
def lock_store(store):
 with open(store/'.save-lock','a+b') as f:
  if os.name=='nt':
   import msvcrt
   if f.tell()==0:f.write(b'0');f.flush()
   f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_LOCK,1)
  else:
   import fcntl
   fcntl.flock(f.fileno(),fcntl.LOCK_EX)
  try:yield
  finally:
   if os.name=='nt':f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
   else:fcntl.flock(f.fileno(),fcntl.LOCK_UN)
def revision(store):
 p=store/'work.json';return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else 'new'
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def reply(self,data,status=200,kind="application/json; charset=utf-8"):
  raw=data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False).encode()
  self.send_response(status);self.send_header("Content-Type",kind);self.send_header("Content-Length",str(len(raw)));self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff");self.end_headers()
  if self.command!="HEAD":self.wfile.write(raw)
 def valid_host(self):
  return self.headers.get('Host') in {'127.0.0.1:'+str(self.server.server_port),'localhost:'+str(self.server.server_port)}
 def do_HEAD(self):self.do_GET()
 def do_GET(self):
  if not self.valid_host():return self.reply({"error":"Local workspace only"},403)
  path=unquote(urlsplit(self.path).path)
  if path=="/api/work":
   try:
    with self.server.write_lock,lock_store(self.server.store):
     p=self.server.store/"work.json";raw=p.read_bytes() if p.exists() else None
     work=json.loads(raw) if raw else None;rev=hashlib.sha256(raw).hexdigest() if raw else "new"
    return self.reply({"work":work,"token":self.server.token,"location":str(self.server.store),"product":PRODUCT,"revision":rev})
   except (OSError,ValueError) as e:return self.reply({"error":"Your saved work could not be read: "+str(e)},500)
  if path=="/api/atlas":
   try:
    with self.server.write_lock,lock_store(self.server.store):work=json.loads((self.server.store/'work.json').read_bytes())
    key=parse_qs(urlsplit(self.path).query).get('id',[''])[0]
    case=next(p['data'] for p in work['projects'] if p['id']==key)
    result=red_threads.validate_case(case)
    if not result['valid']:raise ValueError('; '.join(x['message'] for x in result['errors']))
    return self.reply(render_atlas.render(case).encode('utf-8'),kind='text/html; charset=utf-8')
   except (OSError,ValueError,StopIteration,KeyError) as e:return self.reply({'error':'Could not open this atlas: '+str(e)},400)
  if path=="/health":return self.reply({"product":PRODUCT,"source":str(ROOT)})
  name=path.lstrip('/') or 'index.html';p=(ROOT/name).resolve()
  if not p.is_relative_to(ROOT) or p.suffix.lower() not in {'.json','.html','.js','.css','.png','.jpg','.jpeg','.svg','.ico','.woff2'} or not p.is_file():return self.reply({"error":"Not found"},404)
  try:
   import mimetypes
   return self.reply(p.read_bytes(),kind=mimetypes.guess_type(p.name)[0] or 'application/octet-stream')
  except OSError:return self.reply({"error":"This page asset could not be read"},500)
 def do_POST(self):
  if not self.valid_host():return self.reply({'error':'Local workspace only'},403)
  if self.headers.get('X-Work-Token')!=self.server.token:return self.reply({"error":"Reload this page to reconnect to your workspace."},403)
  if urlsplit(self.path).path=='/api/read-docx':
   try:
    size=int(self.headers.get('Content-Length','0'))
    if not 0<size<=12*1024*1024:raise ValueError('Document limit is 8 MiB.')
    obj=json.loads(self.rfile.read(size));raw=base64.b64decode(obj['data'],validate=True)
    if len(raw)>8*1024*1024:raise ValueError('Document limit is 8 MiB.')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
     if sum(i.file_size for i in z.infolist())>32*1024*1024:raise ValueError('Expanded document is too large.')
     data=z.read('word/document.xml')
     if b'<!DOCTYPE' in data or b'<!ENTITY' in data:raise ValueError('Document contains unsupported XML declarations.')
     root=ET.fromstring(data);ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
     text='\n'.join(''.join(p.itertext()) for p in root.findall('.//w:p',ns))
    return self.reply({'text':text})
   except (ValueError,KeyError,OSError,zipfile.BadZipFile,ET.ParseError) as e:return self.reply({'error':'Could not read this DOCX: '+str(e)},400)
  if urlsplit(self.path).path!='/api/work':return self.reply({"error":"Not found"},404)
  try:
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<=MAX:raise ValueError('This project is too large. Download a backup and keep large source media outside this case collection.')
   raw=self.rfile.read(size);v=json.loads(raw)
   if not isinstance(v,dict) or v.get('app')!=PRODUCT or not isinstance(v.get('projects'),list):raise ValueError('This is not a Red Threads workspace.')
   ids=set()
   for project in v['projects']:
    if not isinstance(project,dict) or not isinstance(project.get('id'),str) or project['id'] in ids:raise ValueError('Each case needs a unique ID.')
    ids.add(project['id']);result=red_threads.validate_case(project.get('data'))
    if not result['valid']:raise ValueError('; '.join(x['path']+': '+x['message'] for x in result['errors'][:5]))
   with self.server.write_lock,lock_store(self.server.store):
    if self.headers.get('If-Match')!=revision(self.server.store):return self.reply({"error":"This case collection changed in another window. Download a backup of your edits, then reload before combining them."},409)
    fd,tmp=tempfile.mkstemp(prefix='.work-',suffix='.tmp',dir=self.server.store)
    try:
     with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
     os.replace(tmp,self.server.store/'work.json')
    finally:
     if os.path.exists(tmp):os.unlink(tmp)
   return self.reply({"saved":True,"revision":hashlib.sha256(raw).hexdigest()})
  except (OSError,ValueError) as e:return self.reply({"error":"Could not save: "+str(e)},400)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--no-browser',action='store_true');ap.add_argument('--port',type=int,default=0);ap.add_argument('--data-home',type=Path);a=ap.parse_args()
 base=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local/share')))/'Collaborative Dynamics'/PRODUCT
 store=(a.data_home or Path(os.environ.get('RED_THREADS_HOME',str(base)))).expanduser().resolve()
 try:
  store.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryFile(dir=store) as f:f.write(b'write check');f.flush()
 except OSError as e:raise SystemExit('Cannot use '+str(store)+': '+str(e)+'\nChoose a writable folder with --data-home. Your existing work has not been changed.')
 with ThreadingHTTPServer(('127.0.0.1',a.port),Handler) as server:
  server.store=store;server.token=secrets.token_urlsafe(32);server.write_lock=threading.Lock()
  url='http://127.0.0.1:'+str(server.server_port)+'/';print(json.dumps({'url':url,'product':PRODUCT,'data_home':str(store)}),flush=True)
  if not a.no_browser:webbrowser.open(url)
  try:server.serve_forever()
  except KeyboardInterrupt:pass
if __name__=='__main__':main()
