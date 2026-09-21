import os
import subprocess
import sys
import threading
import xml.etree.ElementTree as ET
import zipfile
import glob

# Platform kontrolü
IS_WINDOWS = os.name == "nt"
if IS_WINDOWS:
    import ctypes
    import time
    import tkinter as tk
    from tkinter import messagebox
    import winreg

base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

# Çoklu JAR sistemini tespit et (jars klasörü içindeki tüm jarları al)
jars_dir = os.path.join(base_dir, "jars")
if not os.path.exists(jars_dir):
    print(f"[UYARI] '{jars_dir}' klasörü bulunamadı! UYAP jar dosyalarınızın bu klasörde olduğundan emin olun.")
    jar_files = []
else:
    jar_files = glob.glob(os.path.join(jars_dir, "*.jar"))

if not jar_files:
    print("[UYARI] jars klasöründe hiçbir .jar dosyası bulunamadı!")
    
# Classpath oluştur (Windows için ;, Linux/Termux için :)
cp_separator = ";" if IS_WINDOWS else ":"
class_path = base_dir + cp_separator + cp_separator.join(jar_files)

if IS_WINDOWS:
    user_profile = os.environ.get("USERPROFILE", "")
    work_dir = os.path.join(user_profile, "Downloads")
else:
    work_dir = os.path.expanduser("~/storage/downloads")
    if not os.path.exists(work_dir):
        work_dir = "/sdcard/Download"
        if not os.path.exists(work_dir):
            work_dir = os.path.expanduser("~")

# Komut satırından verilen belgeler (çift tıklama: uyap-editor %F). chdir'DEN ÖNCE mutlak yola çevrilir.
DOSYALAR = []
if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
    from urllib.parse import unquote, urlparse
    for _a in sys.argv[1:]:
        if _a.startswith("file://"):
            _a = unquote(urlparse(_a).path)
        _p = os.path.abspath(os.path.expanduser(_a))
        if os.path.exists(_p):
            DOSYALAR.append(_p)
        else:
            print(f"[UYARI] Dosya bulunamadı, atlandı: {_a}")

if os.path.exists(work_dir):
    os.chdir(work_dir)

konsol_modu = sys.stdout and sys.stdout.isatty()
java_adi = "java.exe" if IS_WINDOWS else "java"

# KULLANICI AYARLARI
DARK_MODE = False  # True yaparsanız UYAP karanlık modda açılır (Gece çalışmak için mükemmeldir)
UI_SCALE = "1.2"   # Ekrandaki buton/yazı boyutunu ayarlamak için (1.2, 1.5, 2.0 yapabilirsiniz)

# Tek örnek: çift tıklanan yeni belgeler zaten açık olan editörde açılır (her belge için yeni JVM açılmaz)
INSTANCE_DIR = os.environ.get("UYAP_INSTANCE_DIR") or os.path.expanduser("~/.uyap-editor")

# E-İMZA (rootsuz Android): USB okuyucu köprüsü (eimza/ klasörü). Ayrıntı: eimza/README.md
EIMZA_AKTIF = True
EIMZA_DIR = os.environ.get("EIMZA_DIR") or os.path.expanduser("~/.eimza")
EIMZA_HAZIR = False  # sağlayıcı derlenince True olur

# Tek örnek: editör zaten açıksa belgeleri onda aç ve çık (yeni JVM/boş pencere açma)
def _ornek_bilgisi():
    try:
        d = {}
        with open(os.path.join(INSTANCE_DIR, "instance.properties"), "r", encoding="utf-8") as f:
            for satir in f:
                if "=" in satir:
                    k, v = satir.strip().split("=", 1)
                    d[k] = v
        os.kill(int(d["pid"]), 0)
        return d
    except Exception:
        return None


def ornege_yonlendir(dosyalar):
    import socket
    import time
    # başka bir başlatma sürüyorsa (art arda çift tıklama) örneğin hazır olmasını bekle
    baslangic = os.path.join(INSTANCE_DIR, "starting.pid")
    bekle_sn = 0
    try:
        with open(baslangic, "r") as f:
            bpid = int(f.read().strip())
        os.kill(bpid, 0)
        if bpid != os.getpid() and time.time() - os.path.getmtime(baslangic) < 180:
            bekle_sn = 120
    except Exception:
        pass
    bitis = time.time() + bekle_sn
    while True:
        bilgi = _ornek_bilgisi()
        if bilgi:
            break
        if time.time() >= bitis:
            return False
        time.sleep(0.5)
    try:
        komutlar = [f"OPEN\t{p}" for p in dosyalar] or ["NEW\t"]
        for k in komutlar:
            with socket.create_connection(("127.0.0.1", int(bilgi["port"])), 3) as sk:
                sk.settimeout(20)
                sk.sendall((bilgi["token"] + "\t" + k + "\n").encode("utf-8"))
                cevap = sk.makefile("r", encoding="utf-8").readline().strip()
                if cevap != "OK":
                    return False
        return True
    except Exception as e:
        print(f"[UYARI] Açık editöre iletilemedi ({e}); yeni pencere açılacak.")
        return False


if not IS_WINDOWS and os.environ.get("UYAP_TEK_ORNEK", "1") != "0":
    if ornege_yonlendir(DOSYALAR):
        print("[BİLGİ] Belge zaten açık olan UYAP Editör'de açıldı.")
        sys.exit(0)
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    with open(os.path.join(INSTANCE_DIR, "starting.pid"), "w") as _f:
        _f.write(str(os.getpid()))
    import atexit
    atexit.register(lambda: os.path.exists(os.path.join(INSTANCE_DIR, "starting.pid")) and os.remove(os.path.join(INSTANCE_DIR, "starting.pid")))


# Yollar
base_dir = os.path.dirname(os.path.abspath(__file__))
jars_dir = os.path.join(base_dir, "jars")
derleme_dizini = base_dir

# Termux için varsayılan kaydetme klasörünü Android Belgelerim klasörü yapalım
if not IS_WINDOWS and "com.termux" in os.environ.get("PREFIX", ""):
    uyap_belgelerim = "/sdcard/Documents/UYAP_Belgelerim"
    os.makedirs(uyap_belgelerim, exist_ok=True)
    USER_HOME = uyap_belgelerim
else:
    USER_HOME = base_dir

import shutil

portable_java = os.path.join(base_dir, "jre", "bin", java_adi)
if os.path.exists(portable_java):
    java_exec = portable_java
elif not IS_WINDOWS:
    # Termux'ta paket sistemine (dpkg) sorarak GERÇEK java dosyasının yerini bulalım.
    java_exec = "java"
    try:
        # ÖZELLİKLE Java 11'i arayalım
        dpkg_out = subprocess.check_output(["dpkg-query", "-L", "openjdk-11", "openjdk-11-x", "openjdk-14", "openjdk-21"], stderr=subprocess.DEVNULL).decode("utf-8")
        real_java_paths = [p for p in dpkg_out.splitlines() if p.endswith("/bin/java") or p.endswith("/bin/java.default")]
        
        # İçinde 11 geçenleri en başa al!
        java11_paths = [p for p in real_java_paths if "11" in p or "14" in p]
        deep_paths = [p for p in real_java_paths if "jvm" in p or "opt" in p]
        
        if java11_paths:
            java_exec = java11_paths[0]
        elif deep_paths:
            java_exec = deep_paths[0]
        elif real_java_paths:
            java_exec = real_java_paths[0]
    except Exception:
        pass
    
    if java_exec == "java":
        prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
        termux_java_paths = [
            os.path.join(prefix, "lib", "jvm", "jdk-14.0.2", "bin", "java"),
            os.path.join(prefix, "lib", "jvm", "openjdk-11", "bin", "java"),
            os.path.join(prefix, "lib", "jvm", "java-11-openjdk", "bin", "java"),
            os.path.join(prefix, "lib", "jvm", "openjdk-14", "bin", "java"),
            os.path.join(prefix, "opt", "openjdk-11", "bin", "java"),
            os.path.join(prefix, "lib", "jvm", "openjdk-21", "bin", "java"),
            os.path.join(prefix, "opt", "openjdk", "bin", "java"),
            os.path.join(prefix, "bin", "java"),
        ]
        for p in termux_java_paths:
            if os.path.exists(p):
                java_exec = p
                break
            
    which_java = shutil.which("java")
    print(f"[DEBUG] java_exec path determined: {java_exec}")
    
    try:
        ver_out = subprocess.check_output([java_exec, "-version"], stderr=subprocess.STDOUT).decode("utf-8")
        print(f"[DEBUG] java -version çıktısı:\n{ver_out}")
    except Exception as e:
        print(f"[DEBUG] java -version çalıştırılamadı: {e}")
        if hasattr(e, 'output') and e.output:
            print(f"[DEBUG] Hata çıktısı: {e.output.decode('utf-8', errors='ignore')}")
            
    print(f"[DEBUG] LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', 'AYARLANMAMIŞ')}")

    if java_exec == "java":
        if which_java == "/system/bin/java" or not which_java:
            print("[KRİTİK HATA] Termux üzerinde geçerli bir Java bulunamadı!")
            print("Android'in dahili Java'sı (/system/bin/java) UYAP'ı çalıştıramaz (ProtoLogNative hatası).")
            print("Kurulu olan openjdk paketlerinizin bin/java dosyası PATH'e eklenmemiş veya symlink yok.")
            sys.exit(1)
else:
    java_exec = java_adi

# Kopyalama Modülü
def aninda_udf_oku_ve_kopyala(udf_yolu):
    try:
        if not os.path.exists(udf_yolu):
            print(f"[HATA] Dosya bulunamadı: {udf_yolu}")
            return
        with zipfile.ZipFile(udf_yolu, "r") as arsiv:
            for dosya in arsiv.namelist():
                if "content.xml" in dosya or dosya.endswith(".xml"):
                    with arsiv.open(dosya) as xml_dosyasi:
                        agac = ET.parse(xml_dosyasi)
                        metinler = [elem.text for elem in agac.getroot().iter() if elem.text and elem.text.strip()]
                        tam_metin = "\n".join(metinler)

                        if IS_WINDOWS:
                            r = tk.Tk()
                            r.withdraw()
                            r.clipboard_clear()
                            r.clipboard_append(tam_metin)
                            r.update()
                            r.destroy()
                            print("[BAŞARILI] UDF içeriği Windows panosuna kopyalandı!")
                        else:
                            try:
                                subprocess.run(["termux-clipboard-set"], input=tam_metin.encode("utf-8"), check=True)
                                print("[BAŞARILI] UDF içeriği Termux panosuna kopyalandı!")
                            except Exception:
                                print("[BİLGİ] Panoya kopyalanamadı, metin aşağıda listeleniyor:")
                        print("-" * 50)
                        print(tam_metin[:400] + "\n... [Devamı panoda/metinde]")
                        return
    except Exception as e:
        print(f"[HATA] UDF okuma işlemi başarısız: {e}")

# DOC Aktarım
def udf_to_doc_aktar(udf_yolu):
    try:
        if not os.path.exists(udf_yolu):
            return
        hedef_doc = os.path.splitext(udf_yolu)[0] + "_Disari_Aktarilan.doc"
        with zipfile.ZipFile(udf_yolu, "r") as arsiv:
            for dosya in arsiv.namelist():
                if "content.xml" in dosya or dosya.endswith(".xml"):
                    with arsiv.open(dosya) as xml_dosyasi:
                        agac = ET.parse(xml_dosyasi)
                        paragraflar = [f"<p style='margin-bottom:12px; line-height:1.5;'>{elem.text.strip()}</p>" for elem in agac.getroot().iter() if elem.text and elem.text.strip()]
                        doc_icerik = f"<html><head><meta charset='utf-8'><style>body {{ font-family: 'Times New Roman', serif; font-size: 12pt; padding: 40px; }}</style></head><body>{''.join(paragraflar)}</body></html>"
                        with open(hedef_doc, "w", encoding="utf-8") as f:
                            f.write(doc_icerik)
                        print(f"[BAŞARILI] DOC kaydedildi: {hedef_doc}")
                        return
    except Exception as e:
        print(f"[HATA] DOC aktarım işlemi başarısız: {e}")

import urllib.request
import urllib.error

# Modern Arayüz (FlatLaf) İndirme ve Ayarlama
flatlaf_path = os.path.join(jars_dir, "flatlaf.jar")
if not os.path.exists(flatlaf_path):
    print("[BİLGİ] Modern arayüz motoru (FlatLaf) indiriliyor...")
    try:
        urllib.request.urlretrieve("https://repo1.maven.org/maven2/com/formdev/flatlaf/3.4.1/flatlaf-3.4.1.jar", flatlaf_path)
        print("[BAŞARILI] Modern arayüz motoru indirildi.")
    except Exception as e:
        print(f"[UYARI] FlatLaf indirilemedi, standart arayüz kullanılacak: {e}")

# Jar dosyalarını tekrar listele (flatlaf eklenmiş olabilir)
jar_files = glob.glob(os.path.join(jars_dir, "*.jar"))
cp_separator = ";" if IS_WINDOWS else ":"
class_path = base_dir + cp_separator + cp_separator.join(jar_files)

# Akıcı Kaydırma ve Modern Arayüz Motoru
def java_akici_scroll_hazirla(derleme_dizini, is_windows, cp, dark_mode=False):
    global EIMZA_HAZIR
    laf_class = "com.formdev.flatlaf.FlatDarculaLaf" if dark_mode else "com.formdev.flatlaf.FlatIntelliJLaf"
    
    java_kod_template = """
import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import java.lang.reflect.Method;

public class AkiciUyap {
    private static Timer scrollTimer;
    private static JScrollBar activeBar = null;
    private static double velocity = 0.0;
    private static final double FRICTION = 0.93;
    private static final double BOOST = 0.4;

    // ---- Tek örnek: 127.0.0.1 üzerinde jetonlu küçük servis; "OPEN <yol>" / "NEW" komutlarını alır ----
    private static void openInEditor(final String path) {
        SwingUtilities.invokeLater(new Runnable() {
            public void run() {
                try {
                    Class<?> c = Class.forName("tr.com.havelsan.uyap.system.editor.common.WPAppManager");
                    String[] a = (path == null || path.isEmpty())
                        ? new String[]{"getNewWPInstance", "EDITOR_TYPE_DOCUMENT"}
                        : new String[]{"getNewWPInstance", "EDITOR_TYPE_DOCUMENT", path};
                    try {
                        Method m = c.getDeclaredMethod("a", String[].class);
                        m.setAccessible(true);
                        m.invoke(null, (Object) a);
                    } catch (NoSuchMethodException nsme) {
                        c.getMethod("main", String[].class).invoke(null, (Object) a);
                    }
                    Frame[] fr = Frame.getFrames();
                    for (int i = fr.length - 1; i >= 0; i--) {
                        if (fr[i].isVisible()) { fr[i].toFront(); break; }
                    }
                } catch (Throwable t) {
                    System.out.println("[UYAP] belge acilamadi: " + path + " -> " + t);
                }
            }
        });
    }

    private static void startInstanceServer() {
        final String dir = System.getProperty("uyap.instance.dir");
        if (dir == null || dir.isEmpty()) return;
        try {
            final java.net.ServerSocket ss = new java.net.ServerSocket(0, 8, java.net.InetAddress.getByName("127.0.0.1"));
            java.security.SecureRandom rnd = new java.security.SecureRandom();
            final String token = Long.toHexString(rnd.nextLong()) + Long.toHexString(rnd.nextLong());
            final java.io.File d = new java.io.File(dir);
            d.mkdirs();
            final java.io.File f = new java.io.File(d, "instance.properties");
            String nl = System.lineSeparator();
            String body = "port=" + ss.getLocalPort() + nl + "token=" + token + nl + "pid=" + ProcessHandle.current().pid() + nl;
            java.nio.file.Files.write(f.toPath(), body.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            f.setReadable(false, false); f.setReadable(true, true);
            f.setWritable(false, false); f.setWritable(true, true);
            Runtime.getRuntime().addShutdownHook(new Thread() { public void run() { f.delete(); } });
            Thread t = new Thread(new Runnable() {
                public void run() {
                    while (true) {
                        try {
                            java.net.Socket s = ss.accept();
                            s.setSoTimeout(5000);
                            java.io.BufferedReader br = new java.io.BufferedReader(new java.io.InputStreamReader(s.getInputStream(), java.nio.charset.StandardCharsets.UTF_8));
                            String line = br.readLine();
                            String reply = "ERR";
                            if (line != null) {
                                String[] p = line.split(String.valueOf((char) 9), 3);
                                if (p.length >= 2 && p[0].equals(token)) {
                                    if (p[1].equals("OPEN") && p.length == 3) { openInEditor(p[2]); reply = "OK"; }
                                    else if (p[1].equals("NEW")) { openInEditor(null); reply = "OK"; }
                                }
                            }
                            s.getOutputStream().write((reply + nl).getBytes(java.nio.charset.StandardCharsets.UTF_8));
                            s.getOutputStream().flush();
                            s.close();
                        } catch (Throwable e) {
                            if (ss.isClosed()) return;
                        }
                    }
                }
            }, "uyap-instance-server");
            t.setDaemon(true);
            t.start();
            System.out.println("[UYAP] tek-ornek servisi hazir (port " + ss.getLocalPort() + ")");
        } catch (Throwable t) {
            System.out.println("[UYAP] tek-ornek servisi baslatilamadi: " + t);
        }
    }

    public static void main(String[] args) throws Exception {
        // E-IMZA: Termux USB CCID koprusu (javax.smartcardio TerminalFactory). UYAP kodundan ONCE kaydedilmeli.
        try {
            String eimzaDir = System.getProperty("eimza.dir");
            if (eimzaDir != null && !eimzaDir.isEmpty()) {
                Class<?> pc = Class.forName("eimza.TermuxCcidProvider");
                java.security.Provider prov = (java.security.Provider) pc.getDeclaredConstructor().newInstance();
                java.security.Security.addProvider(prov);
                System.setProperty("javax.smartcardio.TerminalFactory.DefaultType", "TermuxCCID");
                System.out.println("[EIMZA] Termux CCID saglayicisi etkin: " + eimzaDir);
            }
        } catch (Throwable t) {
            System.out.println("[EIMZA] saglayici yuklenemedi: " + t);
        }
        try {
            // Modern Material Expressive Arayüzü (FlatLaf)
            UIManager.setLookAndFeel("LAF_PLACEHOLDER");
            
            // UI Ölçeklendirme ayarları (Termux X11 için daha büyük)
            UIManager.put("ScrollBar.width", 16);
            UIManager.put("Button.arc", 8);
            UIManager.put("Component.arc", 8);
            UIManager.put("ProgressBar.arc", 8);
            UIManager.put("TextComponent.arc", 8);
        } catch (Exception e) {
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception ignored) {}
        }

        UIManager.put("ScrollBar.unitIncrement", 1);
        UIManager.put("ScrollBar.blockIncrement", 16);

        int hz = 120;
        try {
            GraphicsEnvironment ge = GraphicsEnvironment.getLocalGraphicsEnvironment();
            for (GraphicsDevice gd : ge.getScreenDevices()) {
                int rate = gd.getDisplayMode().getRefreshRate();
                if (rate > hz && rate != DisplayMode.REFRESH_RATE_UNKNOWN) hz = rate;
            }
        } catch (Exception ignored) {}
        if (hz > 240) hz = 320;
        final int timerDelay = Math.max(1, (int) Math.round(1000.0 / hz));

        scrollTimer = new Timer(timerDelay, new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                if (activeBar == null || !activeBar.isVisible()) {
                    scrollTimer.stop();
                    velocity = 0;
                    return;
                }
                if (Math.abs(velocity) < 0.1) velocity = 0;
                else velocity *= FRICTION;

                int current = activeBar.getValue();
                int newValue = current + (int) Math.round(velocity);
                int max = activeBar.getMaximum() - activeBar.getVisibleAmount();
                if (newValue < 0) newValue = 0;
                if (newValue > max) newValue = max;
                if (newValue == current && Math.abs(velocity) < 0.1) {
                    scrollTimer.stop();
                    return;
                }
                activeBar.setValue(newValue);
            }
        });

        Toolkit.getDefaultToolkit().addAWTEventListener(new AWTEventListener() {
            public void eventDispatched(AWTEvent event) {
                if (event instanceof MouseWheelEvent) {
                    MouseWheelEvent e = (MouseWheelEvent) event;
                    Component comp = (Component) e.getSource();
                    while (comp != null && !(comp instanceof JScrollPane)) comp = comp.getParent();
                    if (comp instanceof JScrollPane) {
                        JScrollPane pane = (JScrollPane) comp;
                        JScrollBar bar = pane.getVerticalScrollBar();
                        if (bar != null && bar.isVisible()) {
                            e.consume();
                            activeBar = bar;
                            int donus = e.getWheelRotation();
                            int birim = e.getUnitsToScroll();
                            int adim = (birim != 0 ? birim : donus * 3) * 12;
                            velocity += adim * BOOST;
                            if (velocity > 400) velocity = 400;
                            if (velocity < -400) velocity = -400;
                            if (!scrollTimer.isRunning()) scrollTimer.start();
                        }
                    }
                }
            }
        }, AWTEvent.MOUSE_WHEEL_EVENT_MASK);

        Class<?> clazz = Class.forName("tr.com.havelsan.uyap.system.editor.common.WPAppManager");
        Method mainMethod = clazz.getMethod("main", String[].class);
        String[] uyapArgs;
        if (args.length > 0) {
            // Belgenin AÇILMASI için "getNewWPInstance" + mevcut dosya yolu gerekir; editör yalnızca bir dosya alır
            uyapArgs = new String[]{"getNewWPInstance", "EDITOR_TYPE_DOCUMENT", args[0]};
        } else {
            uyapArgs = new String[]{"getNewWPInstance", "EDITOR_TYPE_DOCUMENT"};
        }
        mainMethod.invoke(null, (Object) uyapArgs);
        startInstanceServer();
        for (int i = 1; i < args.length; i++) openInEditor(args[i]);
    }
}
"""
    java_kod = java_kod_template.replace("LAF_PLACEHOLDER", laf_class)
    java_dosya = os.path.join(derleme_dizini, "AkiciUyap.java")
    try:
        with open(java_dosya, "w", encoding="utf-8") as f:
            f.write(java_kod)

        # Derleme önbelleği: kaynaklar değişmediyse javac çalıştırılmaz (çift tıklamada açılış hızlanır)
        import hashlib
        eimza_java = os.path.join(derleme_dizini, "eimza", "TermuxCcidProvider.java")
        _h = hashlib.sha256(java_kod.encode("utf-8"))
        if os.path.exists(eimza_java):
            with open(eimza_java, "rb") as _f:
                _h.update(_f.read())
        hash_degeri = _h.hexdigest()
        hash_dosyasi = os.path.join(derleme_dizini, ".akici.hash")
        sinif_dosyasi = os.path.join(derleme_dizini, "AkiciUyap.class")
        prov_sinif = os.path.join(derleme_dizini, "eimza", "TermuxCcidProvider.class")
        try:
            with open(hash_dosyasi, "r", encoding="utf-8") as _f:
                onceki_hash = _f.read().strip()
        except OSError:
            onceki_hash = ""
        eimza_gerekli = EIMZA_AKTIF and not is_windows and os.path.exists(eimza_java)
        if (onceki_hash == hash_degeri and os.path.exists(sinif_dosyasi)
                and (not eimza_gerekli or os.path.exists(prov_sinif))):
            EIMZA_HAZIR = eimza_gerekli
            print("[BİLGİ] Java bileşenleri güncel, yeniden derleme atlandı.")
            return True

        javac_exec = "javac"
        if IS_WINDOWS:
            portable_javac = os.path.join(derleme_dizini, "jre", "bin", "javac.exe")
            if os.path.exists(portable_javac): javac_exec = portable_javac
        elif not IS_WINDOWS:
            if "java_exec" in globals() and java_exec != "java":
                potential_javac = java_exec.replace("/bin/java", "/bin/javac")
                if os.path.exists(potential_javac):
                    javac_exec = potential_javac
            if javac_exec == "javac":
                try:
                    dpkg_out = subprocess.check_output(["dpkg-query", "-L", "openjdk-11", "openjdk-11-x", "openjdk-14", "openjdk-21"], stderr=subprocess.DEVNULL).decode("utf-8")
                    real_javac_paths = [p for p in dpkg_out.splitlines() if p.endswith("/bin/javac") or p.endswith("/bin/javac.default")]
                    java11_paths = [p for p in real_javac_paths if "11" in p or "14" in p]
                    deep_paths = [p for p in real_javac_paths if "jvm" in p or "opt" in p]
                    
                    if java11_paths:
                        javac_exec = java11_paths[0]
                    elif deep_paths:
                        javac_exec = deep_paths[0]
                    elif real_javac_paths:
                        javac_exec = real_javac_paths[0]
                except Exception:
                    pass
            if javac_exec == "javac":
                prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
                termux_javac_paths = [
                    os.path.join(prefix, "lib", "jvm", "jdk-14.0.2", "bin", "javac"),
                    os.path.join(prefix, "lib", "jvm", "openjdk-11", "bin", "javac"),
                    os.path.join(prefix, "lib", "jvm", "java-11-openjdk", "bin", "javac"),
                    os.path.join(prefix, "lib", "jvm", "openjdk-14", "bin", "javac"),
                    os.path.join(prefix, "opt", "openjdk-11", "bin", "javac"),
                    os.path.join(prefix, "lib", "jvm", "openjdk-21", "bin", "javac"),
                    os.path.join(prefix, "opt", "openjdk", "bin", "javac"),
                    os.path.join(prefix, "bin", "javac"),
                ]
                for p in termux_javac_paths:
                    if os.path.exists(p):
                        javac_exec = p
                        break
        
        # E-imza köprü sağlayıcısı (ayrı derlenir: başarısız olursa editör yine de açılır)
        if eimza_gerekli:
            try:
                subprocess.run(
                    [javac_exec, "--release", "11", "-encoding", "UTF-8", "-cp", cp, eimza_java],
                    cwd=derleme_dizini, check=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                EIMZA_HAZIR = True
                print("[BAŞARILI] E-imza köprü sağlayıcısı derlendi (eimza/TermuxCcidProvider).")
            except Exception as e:
                detay = getattr(e, "stderr", b"") or b""
                print(f"[UYARI] E-imza sağlayıcısı derlenemedi, e-imza devre dışı: {e}\n{detay.decode('utf-8', errors='ignore')}")

        subprocess.run(
            [javac_exec, "--release", "11", "-encoding", "UTF-8", "-cp", cp, java_dosya],
            cwd=derleme_dizini,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("[BAŞARILI] Akıcı kaydırma motoru çoklu-jar sistemiyle derlendi!")
        if not eimza_gerekli or EIMZA_HAZIR:
            with open(hash_dosyasi, "w", encoding="utf-8") as _f:
                _f.write(hash_degeri)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[UYARI] Java derleme hatası (sistem javac'ı bulunamadı veya path hatalı). UYAP normal başlatılacak.\n{e.stderr.decode('utf-8', errors='ignore')}")
        return False
    except Exception as e:
        print(f"[UYARI] Java derlenemedi, UYAP normal başlatılacak: {e}")
        return False

# Argüman işleme
if len(sys.argv) > 1:
    param = sys.argv[1]
    if param == "--oku" and len(sys.argv) > 2:
        aninda_udf_oku_ve_kopyala(sys.argv[2])
        sys.exit(0)
    elif param == "--doc" and len(sys.argv) > 2:
        udf_to_doc_aktar(sys.argv[2])
        sys.exit(0)

# Derleme ve Başlatma
akici_hazir = java_akici_scroll_hazirla(base_dir, IS_WINDOWS, class_path, DARK_MODE)

command = [
    java_exec,
    f"-Duser.home={work_dir}",
    f"-Duser.dir={work_dir}",
    "-Xms512M",
    "-Xmx4096M",
    "--add-opens=java.base/java.util=ALL-UNNAMED",
    "--add-opens=java.base/java.lang=ALL-UNNAMED",
    "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED",
    "--add-exports=jdk.crypto.cryptoki/sun.security.pkcs11.wrapper=ALL-UNNAMED",
    "--add-opens=java.base/java.text=ALL-UNNAMED",
    "--add-opens=java.base/java.io=ALL-UNNAMED",
    "--add-opens=java.desktop/java.awt=ALL-UNNAMED",
    "--add-opens=java.desktop/java.awt.font=ALL-UNNAMED",
    "--add-opens=java.desktop/javax.swing=ALL-UNNAMED",
    "-Dsun.java2d.dpiaware=true",
    f"-Dsun.java2d.uiScale={UI_SCALE}",
    f"-Dflatlaf.uiScale={UI_SCALE}",
    "-Dsun.java2d.d3d=true",
    "-Dswing.volatileImageBufferEnabled=true",
    "-Dawt.useSystemAAFontSettings=on",
    "-Dswing.aatext=true",
    "-cp",
    class_path,
]

if akici_hazir and not IS_WINDOWS:
    command.insert(command.index("-cp"), f"-Duyap.instance.dir={INSTANCE_DIR}")

if akici_hazir and EIMZA_HAZIR:
    # -D bayraklari sinif adindan ONCE gelmeli: -cp'den hemen sonra araya ekle
    command.insert(command.index("-cp"), f"-Deimza.dir={EIMZA_DIR}")
    print(f"[BİLGİ] E-imza köprüsü açık (durum dizini: {EIMZA_DIR}). Köprü çalışmıyorsa 'takılı kart bulunamadı' görürsünüz.")
elif EIMZA_AKTIF and not IS_WINDOWS:
    print("[UYARI] E-imza için sağlayıcı/launcher derlenemedi (javac gerekli): e-imza kapalı.")

if akici_hazir:
    command.append("AkiciUyap")
else:
    command.extend(["tr.com.havelsan.uyap.system.editor.common.WPAppManager", "getNewWPInstance", "EDITOR_TYPE_DOCUMENT"])

if DOSYALAR:
    if akici_hazir:
        command.extend(DOSYALAR)        # ilki editöre, kalanları örnek servisiyle açılır
    else:
        command.append(DOSYALAR[0])     # launcher yoksa: editör tek dosya alır

print(f"[BİLGİ] UYAP Başlatılıyor...\nKomut: {' '.join(command)}")
process = subprocess.Popen(command)
process.wait()
