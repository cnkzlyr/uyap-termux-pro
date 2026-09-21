#!/data/data/com.termux/files/usr/bin/bash
# eimza-agent.jar'i kaynaktan yeniden uretir (JDK 11+ gerekir). Kullanim: bash ~/eimza/agent-src/derle.sh
set -e
D="$(cd "$(dirname "$0")" && pwd)"
T="$(mktemp -d)"
mkdir -p "$T/src/eimza" "$T/src/tr/gov/adalet/service/framework/adalet/eimza/eimzatray/gui" "$T/out"
cp "$D/../TermuxCcidProvider.java" "$D/Agent.java" "$T/src/eimza/"
cp "$D/gui/e.java" "$T/src/tr/gov/adalet/service/framework/adalet/eimza/eimzatray/gui/e.java"
javac --release 11 -encoding UTF-8 -d "$T/out" $(find "$T/src" -name '*.java')
printf 'Premain-Class: eimza.Agent\nCan-Redefine-Classes: false\nCan-Retransform-Classes: false\n' > "$T/manifest.txt"
jar cfm "$D/../eimza-agent.jar" "$T/manifest.txt" -C "$T/out" .
rm -rf "$T"
echo "eimza-agent.jar yenilendi."
