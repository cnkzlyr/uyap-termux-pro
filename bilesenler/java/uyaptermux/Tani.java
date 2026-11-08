package uyaptermux;

import java.awt.Component;
import java.awt.KeyboardFocusManager;
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import javax.swing.text.Caret;
import javax.swing.text.DefaultCaret;
import javax.swing.text.Highlighter;
import javax.swing.text.JTextComponent;

/** Ctrl+Shift+F11: odaktaki metin bileseninin imlec/secim durumunu ~/.uyap-editor/tani-secim.txt'ye yazar. */
final class Tani {
    private Tani() { }

    static void yaz() {
        String d = System.getProperty("uyap.instance.dir", System.getenv().getOrDefault("HOME", ".") + "/.uyap-editor");
        File f = new File(d, "tani-secim.txt");
        try (PrintWriter w = new PrintWriter(new FileWriter(f, true))) {
            KeyboardFocusManager km = KeyboardFocusManager.getCurrentKeyboardFocusManager();
            Component c = km.getFocusOwner();
            w.println("---- " + new java.util.Date() + "  java " + System.getProperty("java.version"));
            w.println("odak penceresi: " + (km.getFocusedWindow() == null ? null : km.getFocusedWindow().getClass().getName()));
            w.println("odak: " + (c == null ? null : c.getClass().getName()));
            if (c instanceof JTextComponent) {
                JTextComponent t = (JTextComponent) c;
                Caret car = t.getCaret();
                w.println("secim: " + t.getSelectionStart() + "-" + t.getSelectionEnd()
                        + " renk=" + t.getSelectionColor() + " secimMetniRengi=" + t.getSelectedTextColor());
                w.println("imlec: " + (car == null ? null : car.getClass().getName())
                        + " secimGorunur=" + (car != null && car.isSelectionVisible())
                        + " gorunur=" + (car != null && car.isVisible())
                        + (car instanceof DefaultCaret ? " guncelleme=" + ((DefaultCaret) car).getUpdatePolicy() : ""));
                Highlighter h = t.getHighlighter();
                w.println("vurgulayici: " + (h == null ? null : h.getClass().getName())
                        + " vurgular=" + (h == null ? 0 : h.getHighlights().length));
                if (h != null) for (Highlighter.Highlight x : h.getHighlights()) {
                    w.println("   " + x.getStartOffset() + "-" + x.getEndOffset() + " " + x.getPainter().getClass().getName());
                }
            }
        } catch (Throwable e) {
            System.err.println("[UYAP] tani yazilamadi: " + e);
        }
    }
}
