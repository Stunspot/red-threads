"""Check static site links and demo/source parity. This is not a browser test."""
from __future__ import annotations
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids=set();self.duplicates=[];self.links=[];self.case_chunks=[];self.in_case=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:
            if a['id'] in self.ids:self.duplicates.append(a['id'])
            self.ids.add(a['id'])
        if tag in {'a','link','use'} and a.get('href'):self.links.append((tag,a['href']))
        if tag in {'img','script','iframe','source','video','audio'} and a.get('src'):self.links.append((tag,a['src']))
        if tag=='script' and a.get('id')=='case-data':self.in_case=True
    def handle_endtag(self,tag):
        if tag=='script':self.in_case=False
    def handle_data(self,data):
        if self.in_case:self.case_chunks.append(data)

def check():
    errors=[];pages={};checked=0
    for required in ['index.html','guide.html','demo.html','.nojekyll','assets/red-threads.png']:
        if not (DOCS/required).is_file():errors.append('Missing site file: '+required)
    for path in DOCS.rglob('*.html'):
        page=Page();page.feed(path.read_text(encoding='utf-8'));pages[path.resolve()]=page
        errors.extend(f'{path.relative_to(ROOT)}: duplicate ID {value}' for value in page.duplicates)
    for path,page in pages.items():
        for tag,link in page.links:
            url=urlsplit(link)
            if url.scheme in {'mailto','tel','data'}:continue
            if url.netloc:
                if url.netloc.lower()!='stunspot.github.io':
                    if tag in {'script','link','iframe'} and url.scheme in {'http','https'}:
                        # A canonical <link> is metadata, not a fetched dependency.
                        if tag!='link' or not link.startswith('https://github.com/'):
                            if tag in {'script','iframe'}:errors.append(f'{path.name}: external executable/frame dependency {link}')
                    continue
                if not url.path.startswith('/red-threads/'):
                    errors.append(f'{path.name}: project URL escapes /red-threads/: {link}');continue
                target=DOCS/unquote(url.path[len('/red-threads/'):])
            elif url.scheme:
                errors.append(f'{path.name}: unsupported link scheme {link}');continue
            elif url.path.startswith('/'):
                if not url.path.startswith('/red-threads/'):
                    errors.append(f'{path.name}: root-relative link will escape project: {link}');continue
                target=DOCS/unquote(url.path[len('/red-threads/'):])
            else:
                target=path.parent/unquote(url.path) if url.path else path
            target=target.resolve()
            if target.is_dir():target=target/'index.html'
            checked+=1
            if not target.is_file():
                errors.append(f'{path.relative_to(ROOT)}: missing target {link}');continue
            if url.fragment and target.suffix=='.html' and target in pages and unquote(url.fragment) not in pages[target].ids:
                errors.append(f'{path.relative_to(ROOT)}: missing anchor {link}')
    demo=pages.get((DOCS/'demo.html').resolve())
    if demo:
        try:
            data=json.loads(''.join(demo.case_chunks))
            source=json.loads((ROOT/'src/red-threads/examples/meridian-case.json').read_text(encoding='utf-8'))
            if data!=source:errors.append('Demo case differs from the canonical fictional fixture.')
        except (ValueError,TypeError) as error:errors.append('Demo data could not be inspected: '+str(error))
    report={'ok':not errors,'html_pages':len(pages),'local_references_checked':checked,'errors':errors,'scope':'Static HTML links, duplicate IDs and fictional demo data parity; no browser, live-URL or assistive-technology observation.'}
    print(json.dumps(report,indent=2))
    return 0 if not errors else 1

if __name__=='__main__':raise SystemExit(check())