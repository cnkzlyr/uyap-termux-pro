// CKZ-HDR/1 | © 2026 Av. Can KIZILYAR⁠​‌​​​​‌‌​‌​​‌​‌‌​‌​‌‌​‌​​​‌​‌‌​‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌‌​​​‌​‌‌​‌​‌​​​​‌‌​‌​​‌​‌‌⁠ | Tüm hakları saklıdır.
// CKZ-HDR/1 | Yazılı izin olmadan çoğaltılamaz, değiştirilemez, dağıtılamaz; bu bildirim kaldırılamaz. Bkz. LICENSE.txt
// CKZ-MUHUR/1 79QShO7J5yn70JDaVOIz8op3atvGv4sGvMkSxbF1temd4xH2KF9bb4nSWU5nwR4dXjr1kHDmLdph0RRE97ozCA==
package eimza;

/** Yazar / telif kimligi. © 2026 Av. Can KIZILYAR — Tüm hakları saklıdır. Bkz. LICENSE.txt */
public final class Kimlik {
    public static final String YAZAR = "Av. Can KIZILYAR";
    public static final String SURUM = "1.0";
    public static final String IZ = "⁠​‌​​​​‌‌​‌​​‌​‌‌​‌​‌‌​‌​​​‌​‌‌​‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌‌​​​‌​‌‌​‌​‌​​​​‌‌​‌​​‌​‌‌⁠";

    private Kimlik() { }

    public static String satir() {
        return "[UYAP-Termux " + SURUM + "] \u00a9 2026 " + YAZAR + " \u2014 T\u00fcm haklar\u0131 sakl\u0131d\u0131r." + IZ;
    }
}
