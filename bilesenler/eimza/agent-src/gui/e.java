package tr.gov.adalet.service.framework.adalet.eimza.eimzatray.gui;

import java.awt.Component;
import java.awt.FlowLayout;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.border.EmptyBorder;

/**
 * Adalet E-Imza uygulamasinin "E-imza Sifrenizi Giriniz" penceresinin yerine gecer (yalnizca web sayfasi PIN'i
 * gondermediginde cagrilir). Termux'ta Swing penceresi Chrome'un arkasinda/gorunmez X ekraninda kaldigi icin
 * once Android'in kendi PIN penceresi (termux-dialog) kullanilir; basarisiz olursa Swing penceresi acilir.
 * EIMZA_PIN_MODE=swing  -> her zaman Swing;  EIMZA_PIN_MODE=android -> yalnizca Android penceresi.
 * PIN hicbir yere yazilmaz/loglanmaz.
 *
 * NOT: Sinif adi uygulamanin (karistirilmis) orijinal sinifiyla ayni olmali; uygulama surumu degisirse
 * bu ad degisebilir - o zaman bu sinif sessizce devre disi kalir ve uygulama kendi penceresini kullanir.
 */
public class e {
    private static final int TIMEOUT_SECONDS = 120;

    public static String a(Component parent) {
        String mode = System.getenv("EIMZA_PIN_MODE");
        if (mode == null) mode = "auto";
        if (!"swing".equalsIgnoreCase(mode)) {
            String[] r = android();
            if (r != null) return r[0];            // r[0] null olabilir = kullanici iptal etti
            if ("android".equalsIgnoreCase(mode)) return null;
        }
        return swing(parent);
    }

    /** @return null = termux-dialog kullanilamadi; {pin} = sonuc (pin null ise iptal) */
    private static String[] android() {
        try {
            ProcessBuilder pb = new ProcessBuilder("termux-dialog", "text", "-t", "E-imza sifresi (PIN)", "-i", "PIN", "-p");
            pb.redirectErrorStream(false);
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
            if (!mc.find()) return null;
            if (Integer.parseInt(mc.group(1)) != -1) return new String[]{null};     // iptal
            Matcher mt = Pattern.compile("\"text\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"").matcher(out);
            if (!mt.find()) return new String[]{null};
            String s = unescape(mt.group(1));
            return new String[]{s.isEmpty() ? null : s};
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

    private static String swing(Component parent) {
        JPasswordField pf = new JPasswordField(10);
        JPanel panel = new JPanel(new FlowLayout());
        panel.setBorder(new EmptyBorder(30, 10, 10, 10));
        panel.add(new JLabel("E-imza \u015eifrenizi Giriniz:"));
        panel.add(pf);
        JOptionPane op = new JOptionPane(panel, JOptionPane.PLAIN_MESSAGE, JOptionPane.OK_CANCEL_OPTION);
        JDialog d = op.createDialog(parent, "E-imza \u015eifre Giri\u015fi");
        d.setAlwaysOnTop(true);
        d.setModal(true);
        d.toFront();
        pf.requestFocusInWindow();
        d.setVisible(true);
        Object v = op.getValue();
        if (v instanceof Integer && (Integer) v == JOptionPane.OK_OPTION) return new String(pf.getPassword());
        return null;
    }
}
