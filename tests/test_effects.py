"""Effects fixture regression tests. All mutations happen in temporary copies."""
import hashlib,json,pathlib,plistlib,shutil,sqlite3,subprocess,sys,tempfile
root=pathlib.Path(sys.argv[1]);script=(pathlib.Path(__file__).resolve().parent.parent / 'fcpchapters').resolve()
def hashes():
 return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
def run(path,*args):
 return subprocess.run(['ruby',str(script),str(path),*args],text=True,capture_output=True)
def change_md(db,pk,key,fn):
 with sqlite3.connect(db) as c:
  mid,blob=c.execute('SELECT m.Z_PK,m.ZDICTIONARYDATA FROM ZCOLLECTION c JOIN ZCOLLECTIONMD m ON c.ZMETADATA=m.Z_PK WHERE c.Z_PK=?',(pk,)).fetchone()
  a=plistlib.loads(blob);o=a['$objects'];d=o[a['$top']['root'].data]
  idx=[o[k.data] for k in d['NS.keys']].index(key);uid=d['NS.objects'][idx].data
  o.append(fn(o[uid]));d['NS.objects'][idx]=plistlib.UID(len(o)-1);c.execute('UPDATE ZCOLLECTIONMD SET ZDICTIONARYDATA=? WHERE Z_PK=?',(plistlib.dumps(a,fmt=plistlib.FMT_BINARY),mid))
before=hashes();r=run(root,'--all','--json');assert r.returncode==0,r.stderr
p={p['project']:p for p in json.loads(r.stdout)['timelines']}
assert len(p)==3
assert p['Multiclip Project']['found_chapters']==11
assert p['Multiclip Project']['chapters'][-1]['seconds']=='1793/10'
assert p['Basic Project']['retimed_clips']==1
assert p['Basic Project']['chapters'][2]['seconds']=='11737/375'
assert p['Transition Project']['transitions']==3
assert p['Transition Project']['retimed_clips']==2
assert p['Transition Project']['chapters'][-1]['seconds']=='541/15'
with tempfile.TemporaryDirectory() as td:
 copy=pathlib.Path(td)/root.name;shutil.copytree(root,copy)
 db=copy/'Event A/Basic Project/CurrentVersion.fcpevent';original=db.read_bytes()
 # Audio retiming with the same supported Time Map must follow the same checks.
 with sqlite3.connect(db) as c:c.execute("UPDATE ZCOLLECTION SET ZTYPE='FFRetimingAudioEffect' WHERE Z_PK=60")
 r=run(copy,'--project','Basic Project','--json');assert r.returncode==0,r.stderr
 assert json.loads(r.stdout)['chapters'][2]['seconds']=='11737/375'
 assert '[Beta] Audio retiming' in r.stderr
 change_md(db,60,'channelData',lambda x:x.replace(b'<value>69940.133333333331</value>',b'<value>0</value>'))
 r=run(copy,'--project','Basic Project','--plain')
 assert r.returncode==1 and 'FFRetimingAudioEffect' in r.stderr and 'non-monotonic' in r.stderr
 db.write_bytes(original)
 # Unreferenced unsupported records must not poison the selected timeline.
 with sqlite3.connect(db) as c:
  c.execute("INSERT INTO ZCOLLECTION (Z_PK,ZTYPE) VALUES (9999,'FFUnknownTimeMap')")
 r=run(copy,'--project','Basic Project','--json');assert r.returncode==0,r.stderr
 # A used unsupported timing class must name both the clip and offending object.
 with sqlite3.connect(db) as c:c.execute("UPDATE ZCOLLECTION SET ZTYPE='FFUnknownTimeMap' WHERE Z_PK=60")
 r=run(copy,'--project','Basic Project','--plain')
 assert r.returncode==1 and not r.stdout and 'Clip A' in r.stderr and 'FFUnknownTimeMap' in r.stderr
 db.write_bytes(original)
 change_md(db,60,'channelData',lambda x:x.replace(b'<value>69940.133333333331</value>',b'<value>0</value>'))
 r=run(copy,'--project','Basic Project','--plain')
 assert r.returncode==1 and 'non-monotonic' in r.stderr and 'Clip A' in r.stderr
 db.write_bytes(original)
 tr=copy/'Event B/Transition Project/CurrentVersion.fcpevent'
 change_md(tr,97,'transitionNilSourceFillType',lambda _:99)
 r=run(copy,'--project','Transition Project','--json')
 assert r.returncode==0,r.stderr
 assert json.loads(r.stdout)['chapters'][-1]['seconds']=='541/15'
 change_md(tr,97,'transitionOverlapType',lambda _:99)
 r=run(copy,'--project','Transition Project','--plain')
 assert r.returncode==1 and 'Shapes Inset' in r.stderr and 'row 97' in r.stderr and 'overlap=99' in r.stderr and 'fill=99' in r.stderr and 'previous=(start)' in r.stderr
assert hashes()==before
print('Passed effects fixture, scoped ownership, detailed errors, non-monotonic retiming rejection, unknown transition rejection and unchanged source. New timing expectations remain provisional pending Final Cut confirmation.')
