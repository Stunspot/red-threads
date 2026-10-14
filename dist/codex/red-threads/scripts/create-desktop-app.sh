#!/bin/sh
set -eu
if [ "$#" -ne 4 ] || [ "$1" != "--atlas" ] || [ "$3" != "--destination" ]; then
 printf '%s\n' 'Use: sh create-desktop-app.sh --atlas "<existing atlas.html>" --destination "<new .app path>"' >&2; exit 1
fi
case "$2" in *.html|*.htm) ;; *) printf '%s\n' 'Choose a rendered atlas HTML file.' >&2;exit 1;;esac
case "$4" in *.app) ;; *) printf '%s\n' 'Choose a new .app filename.' >&2;exit 1;;esac
if [ -e "$4" ] || [ -L "$4" ]; then printf '%s\n' 'That entry already exists; choose another name.' >&2;exit 1;fi
root=$(CDPATH= cd -- "$(dirname -- "$0")/../assets" && pwd -P)
parent=$(CDPATH= cd -- "$(dirname -- "$4")" && pwd -P)
atlas_parent=$(CDPATH= cd -- "$(dirname -- "$2")" && pwd -P)
atlas="$atlas_parent/$(basename -- "$2")"
destination="$parent/$(basename -- "$4")"
if [ ! -f "$atlas" ] || [ ! -f "$root/red-threads-icon.icns" ];then printf '%s\n' 'Keep the complete skill and rendered atlas available.' >&2;exit 1;fi
if [ "$(printf '%s' "$atlas" | wc -l | tr -d ' ')" != 0 ];then printf '%s\n' 'The atlas path cannot contain line breaks.' >&2;exit 1;fi
mkdir -- "$destination"
mkdir -- "$destination/Contents" "$destination/Contents/MacOS" "$destination/Contents/Resources"
cat > "$destination/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>CFBundleName</key><string>RED THREADS</string><key>CFBundleIdentifier</key><string>local.red-threads</string><key>CFBundleExecutable</key><string>atlas</string><key>CFBundleIconFile</key><string>red-threads-icon.icns</string><key>CFBundlePackageType</key><string>APPL</string></dict></plist>
PLIST
cp -- "$root/red-threads-icon.icns" "$destination/Contents/Resources/red-threads-icon.icns"
printf '%s\n' "$atlas" > "$destination/Contents/Resources/target.txt"
cat > "$destination/Contents/MacOS/atlas" <<'LAUNCH'
#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
IFS= read -r target < "$here/../Resources/target.txt"
exec /usr/bin/open "$target"
LAUNCH
chmod 755 "$destination/Contents/MacOS/atlas"
printf '%s\n' "Created RED THREADS entry: $destination"
