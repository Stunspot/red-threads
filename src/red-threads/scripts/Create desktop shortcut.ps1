param([Parameter(Mandatory=$true)][string]$AtlasPath,[Parameter(Mandatory=$true)][string]$ShortcutPath)
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$destination=[IO.Path]::GetFullPath($ShortcutPath)
if([IO.Path]::GetExtension($destination) -ine '.lnk'){throw 'Choose a new .lnk filename.'}
if(Test-Path -LiteralPath $destination){throw 'That entry already exists. Choose a different name; nothing was replaced.'}
$parent=[IO.Path]::GetDirectoryName($destination)
if(-not(Test-Path -LiteralPath $parent -PathType Container)){throw 'Choose an existing destination folder.'}
$launcher=[IO.Path]::GetFullPath($AtlasPath);$icon=[IO.Path]::GetFullPath((Join-Path $root '../assets/red-threads-icon.ico'))
if([IO.Path]::GetExtension($launcher) -notin @('.html','.htm')){throw 'Choose a rendered atlas HTML file.'}
if(-not(Test-Path -LiteralPath $launcher -PathType Leaf) -or -not(Test-Path -LiteralPath $icon -PathType Leaf)){throw 'Keep the complete workspace folder together.'}
$temporary=Join-Path $parent ('.red-threads-'+[Guid]::NewGuid().ToString('N')+'.lnk')
try{
 $entry=(New-Object -ComObject WScript.Shell).CreateShortcut($temporary)
 $entry.TargetPath=$launcher;$entry.WorkingDirectory=[IO.Path]::GetDirectoryName($launcher);$entry.IconLocation=$icon+',0'
 $entry.Description='Open RED THREADS';$entry.Save()
 [IO.File]::Move($temporary,$destination)
 Write-Output ('Created RED THREADS entry: '+$destination)
}finally{if(Test-Path -LiteralPath $temporary){Remove-Item -LiteralPath $temporary}}
