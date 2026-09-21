#!/data/data/com.termux/files/usr/bin/bash
# termux-usb -e tarafindan cagrilir: $1 = fd
DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$DIR/ccid_bridge.py" --probe --fd "$1" 2>&1
