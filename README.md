<!-- CKZ-HDR/1 | © 2026 Av. Can KIZILYAR⁠​‌​​​​‌‌​‌​​‌​‌‌​‌​‌‌​‌​​​‌​‌‌​‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌‌​​​‌​‌‌​‌​‌​​​​‌‌​‌​​‌​‌‌⁠ | Tüm hakları saklıdır. -->
<!-- CKZ-HDR/1 | Yazılı izin olmadan çoğaltılamaz, değiştirilemez, dağıtılamaz; bu bildirim kaldırılamaz. Bkz. LICENSE.txt -->
<!-- CKZ-MUHUR/1 MUHURSUZ -->
# UYAP-Termux Kurulum Paketi

**© 2026 Av. Can KIZILYAR — Tüm hakları saklıdır.** · Resmî değildir (bkz. `LICENSE.txt`, `NOTICE.txt`).

Android telefonda **UYAP Doküman Editörü**'nü, `.udf`/`.usf` dosyalarına çift tıklayarak açmayı ve **USB e-imza
okuyucusuyla** (TBB kırmızı token, ArkSigner vb.) **UYAP Avukat Portal**'a tarayıcıdan girmeyi sağlar.

## Gerekenler
* Android 8+ ve OTG destekli telefon, USB e-imza okuyucu.
* Aşağıdaki **üç uygulama AYNI kaynaktan** (hepsi **F-Droid** veya hepsi **GitHub**) kurulmalıdır. Play Store sürümleri uyumsuzdur:
  **Termux**, **Termux:X11**, **Termux:API**. (İsteğe bağlı: Termux:Boot.)
* ~3 GB boş yer, internet.

## Kurulum
1. Termux'u açın, depolama izni verin: `termux-setup-storage`
2. Paketi indirin ve açın (yalnızca resmî adresten): `https://raw.githubusercontent.com/cnkzlyr/uyap-termux/main/uyap-termux-1.1.zip`
   ```
   cd ~ && unzip -o /sdcard/Download/uyap-termux-1.1.zip && cd uyap-termux-1.1
   ```
3. Kurulumu başlatın: `bash kur.sh` — lisansı okuyup `evet` yazın. (Kurulum başında **mühür doğrulaması** yapılır.)
4. Kurulum bitince Termux'u kapatıp yeniden açın.

**Yazar anahtar parmak izi (resmî değer):** `5141-02F5-BD04-CE67-6AA4-620F-4145-D84C`
Kurulumda görünen parmak izi bununla aynı değilse paket sahte/değiştirilmiş olabilir; kurmayın.

## Kullanım
* **Masaüstü/editör:** `uyap-masaustu` → Termux:X11 açılır; menüde/masaüstünde **UYAP Editör**; `.udf` çift tıklayın.
* **E-imza:** okuyucuyu OTG ile takın, "İzin ver" deyin. Termux her açıldığında köprü ve Adalet E-İmza otomatik başlar.
* **UYAP Avukat Portal:** Termux arka planda açıkken Chrome'dan e-imza ile girin (Chrome "yerel ağ" izni sorarsa verin).
* **Telif/mühür bilgisi:** `uyap-hakkinda`

## Otomatik indirme başarısız olursa
Resmî sayfalardan elle indirip verin:
`bash kur.sh --editor-zip /sdcard/Download/uyapeditor_*_amd64.zip --adalet-deb /sdcard/Download/adalet-eimza-tray*.deb`

## Sorun giderme
`~/.eimza/*.log`, `~/.uyap-editor/editor.log`; tanı: `bash ~/eimza/eimza_tani.sh`.

## Şeffaflık
Yazılım PIN'lerinizi kaydetmez/iletmez ve hiçbir veriyi yazara göndermez. İnternete yalnızca kurulumda resmî sitelerden
dosya indirmek için çıkar. Kaynak dosyalar okunabilir; ancak çoğaltılamaz/değiştirilemez (LICENSE.txt).
