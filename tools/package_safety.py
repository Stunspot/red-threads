"""Portable package names and regular-tree custody; standard library only."""
from __future__ import annotations
import os
import stat
import unicodedata
import zipfile
from pathlib import Path

class PackageError(ValueError):pass

def reject_links(path):
    path=Path(os.path.abspath(path))
    for item in [path,*path.parents]:
        if item.exists() or item.is_symlink():
            st=item.lstat()
            if stat.S_ISLNK(st.st_mode) or getattr(st,'st_file_attributes',0)&0x400:raise PackageError(f'link/reparse path forbidden: {item}')
    # Resolve only after checking the caller path and all ancestors; canonicalizes 8.3 names.
    return path.resolve()

def valid_name(name):
    if not name or name.startswith('/') or '\\' in name:raise PackageError(f'unsafe member: {name!r}')
    parts=name.split('/')
    for part in parts:
        if part in ('','.','..') or part[-1:] in ('.',' ') or any(ord(c)<32 or c in '<>:"|?*' for c in part):raise PackageError(f'nonportable member: {name!r}')
        stem=part.split('.')[0].upper()
        if stem in {'CON','PRN','AUX','NUL','CONIN$','CONOUT$'} or stem in {f'{p}{n}' for p in ('COM','LPT') for n in '123456789¹²³'}:raise PackageError(f'reserved device member: {name!r}')
    return unicodedata.normalize('NFC',name).casefold()

def namespace(entries):
    """Validate all explicit and implicit directories before any payload read/write."""
    seen={};files=set();dirs=set();spellings={}
    for name,is_dir in entries:
        key=valid_name(name)
        if key in seen:raise PackageError(f'duplicate or portable alias: {name!r}')
        seen[key]=name
        if is_dir:dirs.add(key)
        else:files.add(key)
        parts=name.split('/')
        for i in range(1,len(parts)+1):
            raw='/'.join(parts[:i]);canonical=valid_name(raw)
            if canonical in spellings and spellings[canonical]!=raw:raise PackageError(f'portable namespace alias: {raw!r}')
            spellings[canonical]=raw
            if i<len(parts):dirs.add(canonical)
    if files&dirs:raise PackageError(f'file/directory collision: {sorted(files&dirs)}')

def tree_files(root):
    root=reject_links(root)
    if not root.is_dir():raise PackageError(f'expected directory: {root}')
    entries=[];files=[]
    for base,dirs,names in os.walk(root,followlinks=False):
        for name in sorted(dirs+names):
            item=Path(base)/name;st=item.lstat();rel=item.relative_to(root).as_posix()
            if stat.S_ISLNK(st.st_mode) or getattr(st,'st_file_attributes',0)&0x400:raise PackageError(f'link/reparse member: {rel}')
            if not (stat.S_ISDIR(st.st_mode) or stat.S_ISREG(st.st_mode)):raise PackageError(f'nonregular member: {rel}')
            entries.append((rel,stat.S_ISDIR(st.st_mode)))
            if stat.S_ISREG(st.st_mode):files.append(item)
    namespace(entries)
    return sorted(files,key=lambda p:p.relative_to(root).as_posix())

def zip_members(bundle):
    infos=bundle.infolist();entries=[];total=0
    for info in infos:
        name=info.filename[:-1] if info.is_dir() else info.filename
        entries.append((name,info.is_dir()))
        kind=stat.S_IFMT(info.external_attr>>16)
        if kind not in (0,stat.S_IFDIR if info.is_dir() else stat.S_IFREG):raise PackageError(f'nonregular archive member: {name}')
        if info.flag_bits&1:raise PackageError(f'encrypted archive member: {name}')
        total+=info.file_size
    namespace(entries)
    if not infos or total>256*1024*1024:raise PackageError('empty or oversized skill archive')
    return [i for i in infos if not i.is_dir()]

def extract_checked(archive,destination):
    destination=reject_links(destination)
    with zipfile.ZipFile(reject_links(archive)) as bundle:
        infos=zip_members(bundle)
        for info in infos:
            target=destination.joinpath(*info.filename.split('/'));target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(bundle.read(info))
