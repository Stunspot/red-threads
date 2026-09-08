"""Build the RED THREADS release from the maintained skill, companions and artwork."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

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
    output.mkdir(parents=True,exist_ok=True)
    archive=output/f'red-threads-v{version}.zip'
    # Release artifacts are replaceable build outputs. Investigative case tools
    # separately enforce new-file, no-overwrite custody for user evidence.
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files:
            entry=zipfile.ZipInfo('red-threads/'+p.relative_to(skill).as_posix(),date_time=(2026,9,8,0,0,0))
            entry.create_system=3
            entry.compress_type=zipfile.ZIP_DEFLATED
            entry.external_attr=0o644<<16
            z.writestr(entry,p.read_bytes())
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError('Archive integrity check failed.')
        for p in files:
            if z.read('red-threads/'+p.relative_to(skill).as_posix())!=p.read_bytes():
                raise ValueError('Archive member differs from source.')
    assets=[archive]
    for source,name in [(ROOT/'docs/assets/red-threads.png','red-threads.png'),(ROOT/'distribution/install-red-threads.md','install-red-threads.md'),(ROOT/'distribution/red-threads-companion.md','red-threads-companion.md')]:
        destination=output/name
        if source.resolve()!=destination.resolve():
            shutil.copyfile(source,destination)
        assets.append(destination)
    records=[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in assets]
    (output/'SHA256SUMS.txt').write_text(''.join(f"{r['sha256']}  {r['name']}\n" for r in records),encoding='utf-8')
    report={'version':version,'skill_root':'red-threads','runtime_files':len(files),'assets':records,'archive_policy':'Fixed member order, timestamp and platform metadata; compressed bytes may depend on compression-library version.'}
    (output/'release-manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'dist')
    args=parser.parse_args()
    print(json.dumps(build(args.output),indent=2))