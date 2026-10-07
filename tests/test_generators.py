"""Synthetic primary-generator coverage based on the effects fixture; no source mutations."""
import hashlib,json,pathlib,plistlib,shutil,sqlite3,subprocess,sys,tempfile
root=pathlib.Path(sys.argv[1]);script=(pathlib.Path(__file__).resolve().parent.parent / 'fcpchapters').resolve()
project='Transition Project'
def run(path):
 return subprocess.run(['ruby',str(script),str(path),'--project',project,'--json'],capture_output=True,text=True)
def hashes():
 return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
before=hashes();baseline=run(root);assert baseline.returncode==0,baseline.stderr
expected=json.loads(baseline.stdout)
with tempfile.TemporaryDirectory() as td:
 copy=pathlib.Path(td)/root.name;shutil.copytree(root,copy)
 db=copy/'Event B'/project/'CurrentVersion.fcpevent'
 with sqlite3.connect(db) as c:
  # First primary clip has a leading transition and an internal transition after it.
  c.execute("UPDATE ZCOLLECTION SET ZTYPE='FFAnchoredGeneratorComponent' WHERE Z_PK=38")
  c.execute('DELETE FROM Z_3CHILDCOLLECTIONS WHERE Z_3PARENTCOLLECTIONS=38 AND Z_3CHILDCOLLECTIONS=31')
 r=run(copy);assert r.returncode==0,r.stderr
 actual=json.loads(r.stdout)
 assert actual['chapters']==expected['chapters']
 assert actual['clips']==expected['clips']
 assert actual['transitions']==3
 # A primary generator may persist its local origin mapped to parent zero.
 def set_anchor(value):
  with sqlite3.connect(db) as c:
   mid,blob=c.execute('SELECT m.Z_PK,m.ZDICTIONARYDATA FROM ZCOLLECTION c JOIN ZCOLLECTIONMD m ON c.ZMETADATA=m.Z_PK WHERE c.Z_PK=38').fetchone()
   a=plistlib.loads(blob);o=a['$objects'];d=o[a['$top']['root'].data]
   keys=[o[k.data] for k in d['NS.keys']]
   if 'anchorPair' not in keys:
    o.append('anchorPair');d['NS.keys'].append(plistlib.UID(len(o)-1))
    o.append(value);d['NS.objects'].append(plistlib.UID(len(o)-1))
   else:
    o.append(value);d['NS.objects'][keys.index('anchorPair')]=plistlib.UID(len(o)-1)
   c.execute('UPDATE ZCOLLECTIONMD SET ZDICTIONARYDATA=? WHERE Z_PK=?',(plistlib.dumps(a,fmt=plistlib.FMT_BINARY),mid))
 set_anchor('{(235858900/3000),(0/1)}')
 r=run(copy);assert r.returncode==0,r.stderr
 assert json.loads(r.stdout)['chapters']==expected['chapters']
 set_anchor('{(235858900/3000),(5/1)}')
 r=run(copy);assert r.returncode==0,r.stderr
 assert json.loads(r.stdout)['chapters']==expected['chapters']
 assert 'placement uses storyline order' in r.stderr
 for anchor in ['{(3600/1),(21605/6)}','{(54013/15),(1/1)}']:
  set_anchor(anchor)
  r=run(copy);assert r.returncode==0,r.stderr
  assert json.loads(r.stdout)['chapters']==expected['chapters']
  assert json.loads(r.stdout)['clips'][0]['anchor_pair']==anchor
 set_anchor('{(235858900/3000),(0/1)}')
 # Ordinary primary clips can retain anchors too; do not add the parent
 # coordinate again or demand the untrimmed anchor equal the visible start.
 with sqlite3.connect(db) as c:
  c.execute("UPDATE ZCOLLECTION SET ZTYPE='FFAnchoredCollection' WHERE Z_PK=38")
  c.execute('INSERT INTO Z_3CHILDCOLLECTIONS VALUES (38,31)')
 set_anchor('{(0/1),(36139/10)}')
 r=run(copy);assert r.returncode==0,r.stderr
 assert json.loads(r.stdout)['chapters']==expected['chapters']
 assert json.loads(r.stdout)['clips'][0]['anchor_pair']=='{(0/1),(36139/10)}'
 with sqlite3.connect(db) as c:
  c.execute("UPDATE ZCOLLECTION SET ZTYPE='FFAnchoredGeneratorComponent' WHERE Z_PK=38")
  c.execute('DELETE FROM Z_3CHILDCOLLECTIONS WHERE Z_3PARENTCOLLECTIONS=38 AND Z_3CHILDCOLLECTIONS=31')
 # Generator metadata must not hide a nested timeline or unexplained contained items.
 with sqlite3.connect(db) as c:
  c.execute('INSERT INTO Z_3CHILDCOLLECTIONS VALUES (38,31)')
 r=run(copy);assert r.returncode==1
 assert 'Unexpected contained items on generator' in r.stderr
 assert 'Clip D' in r.stderr and 'row 38' in r.stderr
assert hashes()==before
print('Passed: primary generator between leading/internal transitions, generator markers, unchanged following offsets, nested-item rejection, and unchanged source hashes. Fixture is synthetic; reported libraries still need confirmation.')
