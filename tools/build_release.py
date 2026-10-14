"""Build the RED THREADS release from the maintained skill, companions and artwork."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import zipfile
import tempfile
from package_safety import reject_links,tree_files,namespace
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
COPY_DIRS=('src','tools','tests','docs','documentation','distribution','.github')

def write_zip(target,members):
    namespace([(name,False) for path,name in members])
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path,name in sorted(members,key=lambda x:x[1]):
            reject_links(path);entry=zipfile.ZipInfo(name,(2026,9,8,0,0,0));entry.create_system=3;entry.external_attr=(0o100755 if name.endswith(('.sh','.command')) else 0o100644)<<16;entry.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(entry,path.read_bytes(),compresslevel=9)

def build(output: Path) -> dict:
    version=(ROOT/'VERSION').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+',version):
        raise ValueError('VERSION must contain a semantic version such as 0.1.0.')
    skill=ROOT/'src/red-threads'
    required=['SKILL.md','LICENSE.md','TRADEMARKS.md','agents/openai.yaml','assets/atlas.html','scripts/red_threads.py','scripts/investigation_ops.py','scripts/render_atlas.py','examples/meridian-case.json','references/case-format.md','references/review.md','references/evidence-and-reconciliation.md','references/campaign-operations.md','knowledge/index.md','knowledge/record-family-playbook.md','knowledge/anomalies-and-latent-functions.md','knowledge/worked-investigations.md']
    for name in required:
        if not (skill/name).is_file():
            raise ValueError('Missing runtime file: '+name)
    files=sorted((p for p in skill.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}),key=lambda p:p.relative_to(skill).as_posix())
    for p in files:
        if p.is_symlink():
            raise ValueError('Runtime symlink cannot enter a release: '+str(p.relative_to(skill)))
        if p.suffix=='.md':
            for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
                target=target.split('#')[0]
                if target and not re.match(r'[a-z]+:',target) and not (p.parent/target).resolve().exists():
                    raise ValueError('Broken local link: '+target)
    output=reject_links(output)
    if output.exists():raise ValueError('Output already exists; choose a new candidate folder.')
    if output==ROOT or output in ROOT.parents or any((ROOT/name)==output or (ROOT/name) in output.parents for name in COPY_DIRS):raise ValueError('Output overlaps captured source.')
    receipt=json.loads((ROOT/'documentation-authorship.json').read_text(encoding='utf-8'))
    full=json.loads((ROOT/'documentation-manifest.json').read_text(encoding='utf-8'))
    authored=json.loads((ROOT/receipt['documentation_manifest']['path']).read_text(encoding='utf-8'))
    records={x['path']:x for x in receipt['authored_files']}
    if set(records)!=set(authored['customer_docs']) or not set(records)<=set(full['customer_docs']) or receipt['product']['version']!=version or full['version']!=version:raise ValueError('Current documentation identity or scope differs.')
    for name,record in records.items():
        body=reject_links(ROOT/name).read_bytes()
        if hashlib.sha256(body).hexdigest()!=record['sha256'] or len(body)!=record['bytes']:raise ValueError('Authored document differs: '+name)
    references=[receipt['documentation_manifest'],receipt['evidence_packet'],receipt['authoring_response'],receipt['authoring']['capability_snapshot'],*receipt['execution_evidence']]
    for ref in references:
        namespace([(ref['path'],False)]);path=reject_links(ROOT/ref['path'])
        if not path.is_relative_to(ROOT):raise ValueError('Documentation reference escapes source.')
        body=path.read_bytes()
        if hashlib.sha256(body).hexdigest()!=ref['sha256'] or len(body)!=ref['bytes']:raise ValueError('Documentation reference differs: '+ref['path'])
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='red-release-',dir=output.parent) as temporary:
        stage=Path(temporary);packet=stage/('RED-THREADS-v'+version);packet.mkdir()
        for folder in COPY_DIRS:
            tree_files(ROOT/folder);shutil.copytree(ROOT/folder,packet/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.pyo'))
        for name in ['README.md','VERSION','LICENSE.md','TRADEMARKS.md','CHANGELOG.md','CONTRIBUTING.md','SECURITY.md','.gitattributes','.editorconfig','documentation-manifest.json','documentation-authorship.json']:
            shutil.copy2(reject_links(ROOT/name),packet/name)
        for ref in references:
            target=packet/ref['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/ref['path'],target)
        shutil.copytree(skill,packet/'codex/red-threads',ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.pyo'))
        inner=packet/('claude/red-threads-v'+version+'.zip');inner.parent.mkdir()
        write_zip(inner,[(p,'red-threads/'+p.relative_to(skill).as_posix()) for p in files])
        sums=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(packet).as_posix()+'\n' for p in tree_files(packet))
        (packet/'SHA256SUMS.txt').write_text(sums,encoding='utf-8',newline='\n')
        final=stage/'candidate';final.mkdir();archive=final/('red-threads-v'+version+'.zip')
        write_zip(archive,[(p,packet.name+'/'+p.relative_to(packet).as_posix()) for p in tree_files(packet)])
        assets=[archive]
        for source,name in [(ROOT/'docs/assets/red-threads.png','red-threads.png'),(ROOT/'distribution/install-red-threads.md','install-red-threads.md'),(ROOT/'distribution/red-threads-companion.md','red-threads-companion.md')]:
            target=final/name;shutil.copyfile(source,target);assets.append(target)
        records=[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in assets]
        (final/'SHA256SUMS.txt').write_text(''.join(x['sha256']+'  '+x['name']+'\n' for x in records),encoding='utf-8',newline='\n')
        report={'version':version,'skill_root':'codex/red-threads','runtime_files':len(files),'source_complete':True,'assets':records,'archive_policy':'Fixed member order/timestamp/modes; current source/tools/tests/docs/configuration and exact current authorship references included.'}
        (final/'release-manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');final.rename(output)
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(build(args.output),indent=2))