// CKZ-HDR/1 | © 2026 Av. Can KIZILYAR⁠​‌​​​​‌‌​‌​​‌​‌‌​‌​‌‌​‌​​​‌​‌‌​‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌‌​​​‌​‌‌​‌​‌​​​​‌‌​‌​​‌​‌‌⁠ | Tüm hakları saklıdır.
// CKZ-HDR/1 | Yazılı izin olmadan çoğaltılamaz, değiştirilemez, dağıtılamaz; bu bildirim kaldırılamaz. Bkz. LICENSE.txt
// CKZ-MUHUR/1 dcNtDIqc9z5OXjRgmTyf8qInmR0MSdgJmZjDRuu9DRTULNH9v3xB4jJ+DmknGpOAKnNwVSOYziraCVzyo4ihBg==
package tr.gov.adalet.service.framework.adalet.eimza.eimzatray.gui;

import java.awt.Component;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * UYAP-Termux: web sayfasi PIN gondermediginde PIN'i Android'in kendi penceresinden (termux-dialog) alir.
 * Termux'ta uygulamanin masaustu penceresi Chrome'un arkasinda kaldigi icin bu gereklidir.
 * PIN hicbir yere yazilmaz/loglanmaz. termux-dialog kullanilamazsa null doner (uygulama "PIN girilmedi" der).
 *
 * (c) 2026 Av. Can KIZILYAR - Tum haklari saklidir. Bkz. LICENSE.txt
 */
public class e {
    private static final int TIMEOUT_SECONDS = 120;

    public static String a(Component parent) {
        try {
            ProcessBuilder pb = new ProcessBuilder("termux-dialog", "text", "-t", "E-imza sifresi (PIN)", "-i", "PIN", "-p");
            Process p = pb.start();
            p.getOutputStream().close();
            ByteArrayOutputStream bo = new ByteArrayOutputStream();
            Thread t = new Thread(() -> {
                try (InputStream in = p.getInputStream()) {
                    byte[] b = new byte[512];
                    int n;
                    while ((n = in.read(b)) > 0) bo.write(b, 0, n);
                } catch (Exception ignored) { }
            });
            t.setDaemon(true);
            t.start();
            if (!p.waitFor(TIMEOUT_SECONDS, TimeUnit.SECONDS)) {
                p.destroyForcibly();
                return null;
            }
            t.join(1000);
            String out = new String(bo.toByteArray(), StandardCharsets.UTF_8);
            Matcher mc = Pattern.compile("\"code\"\\s*:\\s*(-?\\d+)").matcher(out);
            if (!mc.find() || Integer.parseInt(mc.group(1)) != -1) return null;
            Matcher mt = Pattern.compile("\"text\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"").matcher(out);
            if (!mt.find()) return null;
            String s = unescape(mt.group(1));
            return s.isEmpty() ? null : s;
        } catch (Exception ex) {
            return null;
        }
    }

    private static String unescape(String s) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c != '\\' || i + 1 >= s.length()) { sb.append(c); continue; }
            char n = s.charAt(++i);
            switch (n) {
                case 'n': sb.append('\n'); break;
                case 't': sb.append('\t'); break;
                case 'r': sb.append('\r'); break;
                case 'u':
                    if (i + 4 < s.length()) { sb.append((char) Integer.parseInt(s.substring(i + 1, i + 5), 16)); i += 4; }
                    break;
                default: sb.append(n);
            }
        }
        return sb.toString();
    }
}
