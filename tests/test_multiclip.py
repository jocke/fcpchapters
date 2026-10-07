"""Regression tests for the updated user fixture; mutations affect temp copies only."""
import hashlib, json, pathlib, plistlib, shutil, sqlite3, subprocess, sys, tempfile
from fractions import Fraction
root=pathlib.Path(sys.argv[1])
script=(pathlib.Path(__file__).resolve().parent.parent / 'fcpchapters').resolve()
def hashes():
 return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
def run(path,*args):
 return subprocess.run(['ruby',str(script),str(path),*args],capture_output=True,text=True)
before=hashes()
r=run(root,'--all','--json'); assert r.returncode==0,r.stderr
projects=json.loads(r.stdout)['timelines'];assert len(projects)==3
p=next(p for p in projects if p['project']=='Multiclip Project')
assert p['found_chapters']==11 and p['excluded_chapters']==4
assert [c['name'] for c in p['clips']]==['Clip A','Clip B','Clip C','Clip C','Clip C']
assert [c['seconds'] for c in p['chapters']]==['0/1','19/2','333/10','1793/30','2293/30','88/1','1447/15','1588/15','1904/15','889/6','1671/10','1793/10']
assert sum(Fraction(c['duration']) for c in p['clips'])==Fraction(p['duration'])

def mutate(db,pk,key,value):
 with sqlite3.connect(db) as c:
  mid,blob=c.execute('SELECT m.Z_PK,m.ZDICTIONARYDATA FROM ZCOLLECTION c JOIN ZCOLLECTIONMD m ON c.ZMETADATA=m.Z_PK WHERE c.Z_PK=?',(pk,)).fetchone()
  a=plistlib.loads(blob);o=a['$objects'];d=o[a['$top']['root'].data]
  keys=[o[k.data] for k in d['NS.keys']];uid=d['NS.objects'][keys.index(key)]
  o[uid.data]=value(o[uid.data],o) if callable(value) else value
  c.execute('UPDATE ZCOLLECTIONMD SET ZDICTIONARYDATA=? WHERE Z_PK=?',(plistlib.dumps(a,fmt=plistlib.FMT_BINARY),mid))
with tempfile.TemporaryDirectory() as tmp:
 copy=pathlib.Path(tmp)/root.name;shutil.copytree(root,copy)
 db=copy/'Event A/Multiclip Project/CurrentVersion.fcpevent'
 original=db.read_bytes()
 # The sample's persistent order differs from SQL row order. Reverse it explicitly.
 def reverse(v,o):
  v['NS.objects']=v['NS.objects'][::-1];return v
 mutate(db,36,'$order',reverse)
 r=run(copy,'--project','Multiclip Project','--json');assert r.returncode==0,r.stderr
 q=json.loads(r.stdout)
 drill=next(c for c in q['chapters'] if c['title']=='Starting to drill')
 assert Fraction(drill['seconds'])==Fraction(1373,6)-Fraction(1442,15)+Fraction(19,2)
 db.write_bytes(original)
 # Marker at trimmed clip start is included; marker at clip end is excluded.
 mutate(db,81,'anchorPair','{(0/1),(2420824/30)}') # 80669.3 + 149/6
 r=run(copy,'--project','Multiclip Project','--json');assert r.returncode==0,r.stderr
 q=json.loads(r.stdout);assert q['found_chapters']==10 and q['excluded_chapters']==5
 db.write_bytes(original)
 # A corrupt ordering cannot silently fall back to PK or edge order.
 def remove(v,o):
  v['NS.objects']=v['NS.objects'][:-1];return v
 mutate(db,36,'$order',remove)
 r=run(copy,'--project','Multiclip Project','--plain')
 assert r.returncode==1 and not r.stdout and 'inconsistent order' in r.stderr
 db.write_bytes(original)
 mutate(db,38,'clippedRange','{(139819/2),(2885/30)}')
 r=run(copy,'--project','Multiclip Project','--plain')
 assert r.returncode==1 and not r.stdout and 'do not match timeline duration' in r.stderr
 assert 'Stored Project duration:' in r.stderr and 'difference (stored minus calculated):' in r.stderr and 'Storyline items:' in r.stderr
assert hashes()==before
print('Passed: three real timelines, 11 visible chapters, four trimmed-out records, exact offsets, reordered clips, trim-end exclusion, invalid order/duration rejection, and unchanged fixture.')
