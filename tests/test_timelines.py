import pathlib, tempfile, shutil, sqlite3, plistlib, subprocess, json, hashlib, sys
root=pathlib.Path(sys.argv[1])
script=str((pathlib.Path(__file__).resolve().parent.parent / 'fcpchapters').resolve())
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
def run(root,*args,input=None):
 return subprocess.run(['ruby',script,str(root),*args],input=input,text=True,capture_output=True)
def edit(db,kind,key,value):
 with sqlite3.connect(db) as c:
  pk,data=c.execute('SELECT m.Z_PK,m.ZDICTIONARYDATA FROM ZCOLLECTION c JOIN ZCOLLECTIONMD m ON c.ZMETADATA=m.Z_PK WHERE c.ZTYPE=?',(kind,)).fetchone()
  a=plistlib.loads(data);objects=a['$objects'];d=objects[a['$top']['root'].data]
  keys=[objects[u.data] for u in d['NS.keys']]
  objects[d['NS.objects'][keys.index(key)].data]=value
  c.execute('UPDATE ZCOLLECTIONMD SET ZDICTIONARYDATA=? WHERE Z_PK=?',(plistlib.dumps(a,fmt=plistlib.FMT_BINARY),pk))
with tempfile.TemporaryDirectory() as td:
 copy=pathlib.Path(td)/root.name;shutil.copytree(root,copy)
 db=copy/'Event A/Basic Project/CurrentVersion.fcpevent'
 for duration,rate in [('1/24','24/1'),('1001/24000','24000/1001'),('1/25','25/1'),('1001/30000','30000/1001'),('1/30','30/1'),('1/50','50/1'),('1001/60000','60000/1001'),('1/60','60/1'),('1/120','120/1')]:
  edit(db,'FFSequenceInfo','timecodeFrameDuration',duration)
  r=run(copy,'--json');assert r.returncode==0,r.stderr
  d=json.loads(r.stdout);assert d['frame_rate']==rate
  assert d['chapters'][1]['seconds']=='19/2' and d['chapters'][2]['seconds']=='333/10'
 edit(db,'FFSequenceInfo','timecodeFrameDuration','0/1')
 r=run(copy,'--plain');assert r.returncode==1 and not r.stdout and 'Invalid project range' in r.stderr
 edit(db,'FFSequenceInfo','timecodeFrameDuration','1/30')
 second=copy/'Event A/Second';shutil.copytree(db.parent,second)
 # Duplicate names deliberately exercise numeric selection and all processing.
 r=run(copy,'--json',input='A\n');assert r.returncode==0,r.stderr
 d=json.loads(r.stdout);assert len(d['timelines'])==2
 r=run(copy,'--json',input='bad\n2\n');assert r.returncode==0 and 'Please enter' in r.stderr
 assert json.loads(r.stdout)['location'].endswith('Second/CurrentVersion.fcpevent')
 r=run(copy,'--all','--plain');assert r.returncode==0 and r.stdout.count('00:00 Intro')==2
 r=run(copy,'--json',input='');assert r.returncode==1 and 'No selection received' in r.stderr
 # Unsupported unselected timeline must not prevent selection of a valid one.
 edit(second/'CurrentVersion.fcpevent','FFSequenceInfo','timecodeFrameDuration','0/1')
 r=run(copy,'--json',input='1\n');assert r.returncode==0,r.stderr
 r=run(copy,'--all','--json');assert r.returncode==1
 d=json.loads(r.stdout);assert len(d['timelines'])==1 and len(d['errors'])==1
r=run(root);assert '------------------------------------------------------------\nPaste the chapters into the YouTube description box.' in r.stdout
assert before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
print('Passed: nine rational frame rates, invalid rate, automatic selection, multi-timeline picker/retry/all/EOF, duplicate names, isolated timeline failure, separator spacing, and unchanged source hashes.')
