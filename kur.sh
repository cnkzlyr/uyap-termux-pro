#!/data/data/com.termux/files/usr/bin/bash
# CKZ-HDR/1 | © 2026 Av. Can KIZILYAR⁠​‌​​​​‌‌​‌​​‌​‌‌​‌​‌‌​‌​​​‌​‌‌​‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌‌​​​‌​‌‌​‌​‌​​​​‌‌​‌​​‌​‌‌⁠ | Tüm hakları saklıdır.
# CKZ-HDR/1 | Yazılı izin olmadan çoğaltılamaz, değiştirilemez, dağıtılamaz; bu bildirim kaldırılamaz. Bkz. LICENSE.txt
# CKZ-MUHUR/1 MUHURSUZ
# UYAP-Termux Kurulum Paketi — ana kurulum betigi.
#   bash kur.sh [--kabul] [--hafif] [--deneme] [--yine-de]
#               [--editor-zip YOL] [--adalet-deb YOL] [--parmak XXXX-XXXX-...] [--paket-atla]
#   --kabul        lisansi okudugunuzu ve kabul ettiginizi onaylar (soru sormaz)
#   --hafif        XFCE yerine hafif fluxbox masaustu
#   --deneme       hicbir sey degistirmeden adimlari yazar
#   --yine-de      muhur dogrulamasi BASARISIZ/YOK olsa da devam eder (yazar onayi olmadan; kendi sorumlulugunuzdadir)
#   --editor-zip   resmi UYAP Editor zip'ini (uyapeditor_*_amd64.zip) elle verin (otomatik indirme calismazsa)
#   --adalet-deb   resmi adalet-eimza-tray*.deb dosyasini elle verin
#   --parmak       yazarin resmi sayfasinda yayimlanan anahtar parmak izi (dogrulamayi sabitler)
set -u
KOK="$(cd "$(dirname "$0")" && pwd)"
. "$KOK/bilesenler/eimza/marka.sh" 2>/dev/null || { echo "marka.sh eksik: paket bozuk."; exit 1; }

KABUL=0; HAFIF=0; DENEME=0; YINEDE=0; EDITOR_ZIP=""; ADALET_DEB=""; PARMAK="${CKZ_PARMAK:-}"; PAKETATLA=0
while [ $# -gt 0 ]; do
  case "$1" in
    --kabul) KABUL=1 ;; --hafif) HAFIF=1 ;; --deneme) DENEME=1 ;; --yine-de) YINEDE=1 ;; --paket-atla) PAKETATLA=1 ;;
    --editor-zip) shift; EDITOR_ZIP="${1:-}" ;;
    --adalet-deb) shift; ADALET_DEB="${1:-}" ;;
    --parmak) shift; PARMAK="${1:-}" ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "Bilinmeyen secenek: $1"; exit 2 ;;
  esac
  shift
done
run() { if [ "$DENEME" = "1" ]; then echo "[deneme] $*"; else "$@"; fi; }
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
HATA="$HOME/uyap-termux-kurulum-hatalar.txt"; : > "$HATA" 2>/dev/null
fail() { echo "  ! $*"; echo "$*" >> "$HATA"; }

ckz_banner
echo

# ---------------------------------------------------------------- 0) ortam
if [ "$DENEME" != "1" ] && [ ! -d /data/data/com.termux ] && [ -z "${UYAP_TEST_ORTAMI:-}" ]; then
  echo "Bu paket yalnizca Android'deki Termux (F-Droid/GitHub surumu) icindir."; exit 1
fi
case "$(uname -m)" in aarch64|arm64) ;; *) echo "(uyari) Islemci $(uname -m): paket arm64 icin hazirlandi." ;; esac
[ "$KABUL" = "1" ] || { [ -t 0 ] || { echo "Etkilesimli degil: lisansi kabul ediyorsaniz --kabul ekleyin."; exit 1; }; }

# ---------------------------------------------------------------- 1) lisans
echo "== 1/7 Lisans"
sed -n '1,28p' "$KOK/LICENSE.txt"
echo "   ... (tamami: $KOK/LICENSE.txt ; ucuncu taraf bilesenler: NOTICE.txt)"
if [ "$KABUL" != "1" ]; then
  printf '\nLisansi okudum ve kabul ediyorum (evet/hayir): '; read -r c
  case "$c" in evet|EVET|Evet|e|E) ;; *) echo "Kurulum iptal edildi."; exit 1 ;; esac
fi

# ---------------------------------------------------------------- 2) temel paketler + muhur
echo "== 2/7 Temel paketler ve mühür doğrulaması"
if [ "$PAKETATLA" != "1" ]; then run pkg update -y; run pkg install -y python unzip zip curl tar dpkg || fail "temel paketler kurulamadi"; fi
command -v python3 >/dev/null 2>&1 || { echo "python3 yok."; [ "$DENEME" = "1" ] || exit 1; }
if command -v python3 >/dev/null 2>&1; then
  pin=(); [ -n "$PARMAK" ] && pin=(--pub-parmak "$PARMAK")
  python3 "$KOK/tools/dogrula.py" "$KOK" "${pin[@]}"; rc=$?
  echo "   Yukaridaki parmak izini yazarin RESMI sayfasindaki degerle karsilastirin."
  if [ $rc -eq 0 ] && [ -z "$PARMAK" ]; then
    if [ "$KABUL" != "1" ]; then
      printf '   Parmak izi resmi sayfadaki degerle AYNI mi? (evet/hayir): '; read -r c
      case "$c" in evet|EVET|Evet|e|E) ;; *) echo "   Kurulum durduruldu."; exit 3 ;; esac
    else
      echo "   (uyari) --parmak verilmedi: parmak izi elle dogrulanmadi."
    fi
  fi
  if [ $rc -ne 0 ]; then
    echo
    echo "   !!! Bu kopya yazar (Av. Can KIZILYAR) tarafindan dogrulanamadi. Degistirilmis/sahte olabilir."
    if [ "$YINEDE" != "1" ]; then echo "   Kurulum durduruldu. Resmi kaynaktan tekrar indirin. (Bilincli devam: --yine-de)"; [ "$DENEME" = "1" ] || exit 3; fi
    echo "   --yine-de: devam ediliyor; bu kurulum 'ONAYSIZ' olarak isaretlenecek."
    ONAYSIZ=1
  fi
fi
ONAYSIZ="${ONAYSIZ:-0}"

# ---------------------------------------------------------------- 3) depolar ve paketler
echo "== 3/7 Depolar ve paketler (uzun surebilir)"
PAKETLER="python libusb termux-api openjdk-11 openjdk-21 openjdk-21-x xorg-server-xvfb termux-x11-nightly"
[ "$HAFIF" = "1" ] && PAKETLER="$PAKETLER fluxbox" || PAKETLER="$PAKETLER xfce4 xfce4-terminal thunar"
if [ "$PAKETATLA" != "1" ]; then
  run pkg install -y x11-repo tur-repo || fail "x11-repo/tur-repo kurulamadi"
  run pkg update -y
  for p in $PAKETLER; do
    if [ "$DENEME" = "1" ]; then echo "[deneme] pkg install -y $p"; continue; fi
    dpkg -s "$p" >/dev/null 2>&1 && continue
    pkg install -y "$p" >/dev/null 2>&1 && echo "   + $p" || fail "paket kurulamadi: $p"
  done
fi

# ---------------------------------------------------------------- 4) resmi UYAP Editor
T="$(mktemp -d "${TMPDIR:-$PREFIX/tmp}/uyapkur.XXXXXX")"; trap 'rm -rf "$T"' EXIT
echo "== 4/7 UYAP Doküman Editörü (T.C. Adalet Bakanlığı) — resmî kaynaktan indirilir, pakete dahil DEĞİLDİR"
editor_indir() {
  if [ -z "$EDITOR_ZIP" ] && [ -f "$HOME/jars/editor_lib.jar" ]; then echo "   jar'lar zaten mevcut: ~/jars"; return 0; fi
  local zip="$EDITOR_ZIP"
  if [ -z "$zip" ]; then
    local sayfa url
    sayfa="$(curl -fsSL --max-time 40 https://uyap.gov.tr/UYAP-Editor 2>/dev/null)" || { fail "uyap.gov.tr sayfasina ulasilamadi"; return 1; }
    url="$(printf '%s' "$sayfa" | grep -oE 'https://rayp\.adalet\.gov\.tr/[A-Za-z0-9_./-]*uyapeditor_[0-9.]+_amd64\.zip' | head -1)"
    [ -n "$url" ] || { fail "resmi sayfada Pardus/Debian paketi baglantisi bulunamadi (sayfa degismis olabilir)"; return 1; }
    echo "   indiriliyor: $url"
    curl -fL --max-time 1200 -o "$T/editor.zip" "$url" || { fail "editor indirilemedi"; return 1; }
    zip="$T/editor.zip"
  fi
  echo "   sha256: $(sha256sum "$zip" | cut -d' ' -f1)"
  mkdir -p "$T/ed" && unzip -q -o "$zip" -d "$T/ed" || { fail "editor zip'i acilamadi"; return 1; }
  for d in $(find "$T/ed" -name '*.deb' 2>/dev/null); do
    case "$(basename "$d")" in *cups*) continue ;; esac
    dpkg-deb --fsys-tarfile "$d" | tar -x -C "$T/ed" --wildcards '*.jar' 2>/dev/null
  done
  python3 - "$T/ed" "$HOME/jars" <<'PY'
import os, shutil, sys, zipfile
kok, hedef = sys.argv[1:3]
ana = None
for r, _, fs in os.walk(kok):
    for f in fs:
        if f.endswith(".jar"):
            try:
                with zipfile.ZipFile(os.path.join(r, f)) as z:
                    if "tr/com/havelsan/uyap/system/editor/common/WPAppManager.class" in z.namelist():
                        ana = r
            except zipfile.BadZipFile:
                pass
if not ana:
    print("   HATA: paketin icinde editor JAR'i (WPAppManager) bulunamadi"); sys.exit(1)
os.makedirs(hedef, exist_ok=True)
n = 0
for f in sorted(os.listdir(ana)):
    if f.endswith(".jar"):
        shutil.copy2(os.path.join(ana, f), os.path.join(hedef, f)); n += 1; print("   ->", f)
print("   %d jar ~/jars altina kopyalandi." % n)
PY
}
if [ "$DENEME" = "1" ]; then echo "[deneme] editor_indir"; else editor_indir || echo "   (Editor otomatik kurulamadi. Elle: bash kur.sh --editor-zip /yol/uyapeditor_*_amd64.zip --paket-atla --kabul)"; fi

# ---------------------------------------------------------------- 5) bilesenler
echo "== 5/7 UYAP-Termux bileşenleri"
if [ "$DENEME" != "1" ]; then
  [ -f "$HOME/ue.py" ] && cp -a "$HOME/ue.py" "$HOME/ue.py.onceki" 2>/dev/null
  cp -a "$KOK/bilesenler/ue.py" "$HOME/ue.py"
  mkdir -p "$HOME/eimza"; cp -a "$KOK/bilesenler/eimza/." "$HOME/eimza/"
  chmod +x "$HOME"/eimza/*.sh "$HOME"/eimza/*.py 2>/dev/null
  rm -rf "$HOME/.ckz-kurulum"; mkdir -p "$HOME/.ckz-kurulum"; cp -a "$KOK/." "$HOME/.ckz-kurulum/"
  mkdir -p "$HOME/.ckz-durum"; rm -f "$HOME/.ckz-durum/ONAYSIZ"
  [ "$ONAYSIZ" = "1" ] && echo "ONAYSIZ kurulum: yazar muhru dogrulanamadi ($(date '+%F %T'))" > "$HOME/.ckz-durum/ONAYSIZ"
  { ckz_satir; echo "kurulum: $(date '+%F %T')  surum: $CKZ_SURUM"; } > "$HOME/.ckz-durum/KURULUM.txt"
  echo "   ue.py, eimza/ ve mühür kopyası (~/.ckz-kurulum) yerleştirildi."
else echo "[deneme] bilesenler -> ~/ue.py, ~/eimza/"; fi

# ---------------------------------------------------------------- 6) Adalet E-Imza
echo "== 6/7 Adalet E-İmza (T.C. Adalet Bakanlığı) — resmî kaynaktan"
adalet_indir() {
  [ -z "$ADALET_DEB" ] && [ -f "$HOME/eimza/adalet/eimza-tray.jar" ] && { echo "   zaten kurulu"; return 0; }
  local deb="$ADALET_DEB"
  [ -n "$deb" ] || deb="$(ls -1 "$HOME"/storage/downloads/adalet-eimza-tray*.deb /sdcard/Download/adalet-eimza-tray*.deb 2>/dev/null | sort -V | tail -1)"
  if [ -z "$deb" ]; then
    local json url
    json="$(curl -fsSL --max-time 30 https://cdn.uyap.gov.tr/framework/public/latest.json 2>/dev/null)" || json=""
    url="$(printf '%s' "$json" | python3 -c '
import sys, json, re
try: d = json.load(sys.stdin)
except Exception: sys.exit(0)
c = []
def w(x):
    if isinstance(x, dict): [w(v) for v in x.values()]
    elif isinstance(x, list): [w(v) for v in x]
    elif isinstance(x, str) and re.search(r"\.deb($|\?)", x): c.append(x)
w(d)
c.sort(key=lambda s: ("amd64" not in s, "linux" not in s.lower()))
if c:
    u = c[0]
    print(u if u.startswith("http") else "https://cdn.uyap.gov.tr" + (u if u.startswith("/") else "/" + u))
' 2>/dev/null)"
    if [ -n "$url" ]; then
      echo "   indiriliyor: $url"; curl -fL --max-time 900 -o "$T/adalet.deb" "$url" && deb="$T/adalet.deb" || fail "adalet .deb indirilemedi"
    fi
  fi
  if [ -z "$deb" ]; then
    fail "Adalet E-Imza paketi bulunamadi. https://eimza.adalet.gov.tr adresinden Linux (.deb) surumunu Download klasorune indirip: bash ~/eimza/adalet_kur.sh"
    return 1
  fi
  bash "$HOME/eimza/adalet_kur.sh" "$deb"
}
if [ "$DENEME" = "1" ]; then echo "[deneme] adalet_indir"; else adalet_indir || true; fi

# ---------------------------------------------------------------- 7) entegrasyon
echo "== 7/7 Otomatik başlatma, masaüstü ve dosya ilişkilendirme"
if [ "$DENEME" != "1" ]; then
  bash "$HOME/eimza/kur.sh"
  mkdir -p "$HOME/.local/bin" "$HOME/.shortcuts"
  printf '#!/data/data/com.termux/files/usr/bin/bash\nMASAUSTU=%s exec bash "$HOME/eimza/xfce_baslat.sh"\n' "$([ "$HAFIF" = 1 ] && echo fluxbox || echo xfce)" > "$HOME/.local/bin/uyap-masaustu"
  chmod +x "$HOME/.local/bin/uyap-masaustu"; cp "$HOME/.local/bin/uyap-masaustu" "$HOME/.shortcuts/UYAP-Masaustu" 2>/dev/null
else echo "[deneme] bash ~/eimza/kur.sh ; uyap-masaustu kisayolu"; fi

echo
ckz_banner
[ "$ONAYSIZ" = "1" ] && echo "!!! ONAYSIZ KURULUM: bu kopya yazar mühürüyle doğrulanamadı."
if [ -s "$HATA" ]; then echo "Bazı adımlar tamamlanamadı ($HATA):"; cat "$HATA"; else rm -f "$HATA"; echo "Hata yok."; fi
cat <<'SON'

SIRADAKI ADIMLAR
  1) Android: Termux, Termux:X11 ve Termux:API için pil optimizasyonunu KAPATIN; Termux'a
     "diğer uygulamaların üzerinde göster" izni verin. Termux:API'yi bir kez açın.
  2) Masaüstü:   uyap-masaustu        (Termux:X11 açılır; ".udf" dosyalarına çift tıklayın)
  3) E-imza okuyucusunu OTG ile takın; "İzin ver" deyin (mümkünse "varsayılan olarak kullan").
  4) Tarayıcıdan UYAP Avukat Portal → e-imza ile giriş (Termux arka planda açık kalsın).
  5) Telif ve mühür bilgisi:   uyap-hakkinda
SON
