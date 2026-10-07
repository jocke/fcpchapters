"""Event reporting and compositor regression tests; temporary copies only."""
import json,pathlib,plistlib,shutil,sqlite3,subprocess,sys,tempfile
root=pathlib.Path(sys.argv[1]);script=(pathlib.Path(__file__).resolve().parent.parent / 'fcpchapters').resolve()
def run(p,*args):
 return subprocess.run(['ruby',str(script),str(p),*args],capture_output=True,text=True)
with tempfile.TemporaryDirectory() as td:
 p=pathlib.Path(td)/root.name;shutil.copytree(root,p)
 empty=p/'Empty Event';empty.mkdir()
 shutil.copy2(p/'Event A/CurrentVersion.fcpevent',empty/'CurrentVersion.fcpevent')
 db=p/'Event B/Transition Project/CurrentVersion.fcpevent'
 with sqlite3.connect(db) as c:
  mid,blob=c.execute('SELECT m.Z_PK,m.ZDICTIONARYDATA FROM ZCOLLECTION c JOIN ZCOLLECTIONMD m ON m.Z_PK=c.ZMETADATA WHERE c.Z_PK=142').fetchone()
  a=plistlib.loads(blob);o=a['$objects'];d=o[a['$top']['root'].data];keys=[o[k.data] for k in d['NS.keys']]
  for key,value in [('effectType','effect.video.compositor'),('displayName','Compositing')]:
   o.append(value);d['NS.objects'][keys.index(key)]=plistlib.UID(len(o)-1)
  c.execute('UPDATE ZCOLLECTIONMD SET ZDICTIONARYDATA=? WHERE Z_PK=?',(plistlib.dumps(a,fmt=plistlib.FMT_BINARY),mid))
  c.execute("UPDATE ZCOLLECTION SET ZTYPE='FFHeBlendEffect' WHERE Z_PK=142")
 r=run(p,'--all','--json');assert r.returncode==0,r.stderr
 data=json.loads(r.stdout);assert len(data['timelines'])==3 and data['empty_events']==['Empty Event']
 assert 'Event "Empty Event": No Projects found in the Event. Nothing to output.' in r.stderr
 assert 'Event "Event A": No Projects' not in r.stderr
 with sqlite3.connect(db) as c:c.execute("UPDATE ZCOLLECTION SET ZTYPE='FFUnknownTimeMap' WHERE Z_PK=142")
 r=run(p,'--all');assert r.returncode==1
 assert 'No chapter output for this Project.\nReason:\n  ' in r.stdout and 'FFUnknownTimeMap' in r.stdout
 # Keep only event databases: empty projects are normal, not an extraction error.
 for event in [p/'Event A',p/'Event B']:
  for child in event.iterdir():
   if child.is_dir():shutil.rmtree(child)
 r=run(p,'--json');assert r.returncode==0,r.stderr
 data=json.loads(r.stdout);assert data['timelines']==[] and len(data['empty_events'])==3
 r=run(p,'--plain');assert r.returncode==0 and r.stdout==''
print('Passed compositor handling, empty/populated Event distinction, local failure explanation, and empty-Library JSON/plain behavior.')
