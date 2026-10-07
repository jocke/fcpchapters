"""Diagnostic export must survive timing failures and preserve full relationships."""
import hashlib,json,pathlib,shutil,sqlite3,subprocess,sys,tempfile
root=pathlib.Path(sys.argv[1]);script=(pathlib.Path(__file__).resolve().parent.parent / 'fcpchapters').resolve()
def run(path,*args):
 return subprocess.run(['ruby',str(script),str(path),*args],capture_output=True,text=True)
with tempfile.TemporaryDirectory() as td:
 copy=pathlib.Path(td)/root.name;shutil.copytree(root,copy)
 db=copy/'Event A/Basic Project/CurrentVersion.fcpevent'
 with sqlite3.connect(db) as c:c.execute("UPDATE ZCOLLECTION SET ZTYPE='FFUnknownTimeMap' WHERE Z_PK=60")
 before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in copy.rglob('*') if p.is_file()}
 r=run(copy,'--all','--diagnostics');assert r.returncode==0,r.stderr
 data=json.loads(r.stdout);assert data['diagnostic_format']==1 and len(data['projects'])==3
 p=next(p for p in data['projects'] if p['project']=='Basic Project')
 assert 'FFUnknownTimeMap' in p['extraction_error']
 with sqlite3.connect(db) as c:
  assert len(p['objects'])==c.execute('SELECT COUNT(*) FROM ZCOLLECTION').fetchone()[0]
  assert len(p['relationships'])==c.execute('SELECT COUNT(*) FROM Z_3CHILDCOLLECTIONS').fetchone()[0]
 secondary=next(p for p in data['projects'] if p['project'] == 'Transition Project')
 maps=[o['metadata']['channelData'] for o in secondary['objects'] if o['type']=='FFRetimingVideoEffect']
 assert len(maps)==2 and all('Time Map' in x for x in maps)
 assert not any('data' in o or 'bookmark' in o['metadata'] for p in data['projects'] for o in p['objects'])
 assert before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in copy.rglob('*') if p.is_file()}
print('Passed: valid diagnostic JSON despite extraction failure, complete object/relationship counts, retiming XML, bounded metadata selection and unchanged source.')
