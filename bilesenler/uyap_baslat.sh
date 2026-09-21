#!/data/data/com.termux/files/usr/bin/bash
# (Eski yontem: yalnizca Termux:X11 + fluxbox ile). XFCE kullaniyorsaniz masaustundeki "UYAP Editör" simgesi yeterli.
# E-imza koprusu + Adalet E-Imza (izin penceresi Termux ekraninda cikar -> X11'den ONCE)
[ -f "$HOME/eimza/otobaslat.sh" ] && bash "$HOME/eimza/otobaslat.sh"

termux-x11 :0 &
sleep 1
DISPLAY=:0 fluxbox &
sleep 1
echo "Termux:X11 uygulamasına otomatik geçiş yapılıyor..."
am start -n com.termux.x11/com.termux.x11.MainActivity

DISPLAY=:0 python ~/ue.py "$@"
