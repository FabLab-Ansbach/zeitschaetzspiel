# Zeitschätzspiel

Es handelt sich um ein einfaches Zeitschätzspiel, bei dem eine vorgegebene Zeit möglichst genau abgeschätzt werden muss.\
Zur Zeitmessung und Auswertung der Eingaben wird ein Arduino verwendet. Die grafische Darstellung und die Verwaltung der
Spielergebnisse erfolgt wahlweise über die **Web-App** (empfohlen) oder über das ältere Python Programm. Die Kommunikation
zwischen Arduino und Oberfläche erfolgt in beiden Fällen textbasiert über eine Serielle Schnittstelle.

👉 **[Web-App starten](https://fablab-ansbach.github.io/zeitschaetzspiel/)** (Chrome oder Edge)

## Benötigtes Material

- Arduino mit USB-Schnittstelle
- Taster (z.B. Grobhandtaster)

## Hardwareaufbau

Der Hardwareaufbau ist denkbar einfach. Dazu wird der verwendete Taster mit GND und Pin2 am Arduino verbunden.\
Es wird kein zusätzlicher Pull-Up Widerstand benötigt, da der interne Pull-Up Widerstand vom Arduino verwendet wird.

## Abhängigkeiten

### Arduino Sketch

Der Arduino Sketch greift ausschließlich auf Systemfunktionen zu und benötigt keine zusätzlichen Librarys.

### Web-App

- Browser mit Web Serial API: Chrome, Edge, Opera oder ein neuerer Firefox
- **Nicht als Snap installiert** (siehe unten)
- Aufruf über HTTPS oder localhost
- Benutzer in der Gruppe ``dialout`` (``sudo usermod -aG dialout $USER``, danach neu anmelden)
- Für die Entwicklung zusätzlich Node.js 22+

#### Snap-Browser können keine seriellen Ports

Unter Ubuntu kommen Firefox und Chromium als Snap. Deren AppArmor-Profil erlaubt nur die udev-Majors
4 und 5 (``/dev/tty``, ``/dev/ttyS*``) – ein USB-Seriell-Adapter (``/dev/ttyUSB*``, Major 188) oder ein
Arduino mit CDC-ACM (``/dev/ttyACM*``, Major 166) taucht in der Portauswahl deshalb gar nicht erst auf.
In der Liste stehen dann nur Bluetooth-Geräte, die über BlueZ gefunden werden.

Das lässt sich nicht per ``snap connect`` reparieren: das Interface ``serial-port`` hat auf einem
normalen Desktop keinen Slot. Abhilfe schafft nur ein Browser außerhalb des Snaps, z.B. Google Chrome
als .deb:

``` BASH
wget -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install /tmp/chrome.deb
```

### Python Frontend (optional, Fallback)

- python3
- pip3
- tkinter
- pygame

## Installation

``` BASH
sudo apt update
sudo apt install python3 python3-pip python3-tk python3-pygame python3-serial
git clone https://git.dorf.cloud/lukasdietz/Zeitschaetzspiel.git
cd ../Zeitschaetzspiel
```

Den Arduino Sketch ``../Zeitschaetzspiel/Arduino/Zeitschaetzspiel.ino`` auf den Aruino übertragen und ggf. prüfen, ob eine
serielle Kommunikation (9600 Baud) mit dem Arduino möglich ist.

## Verwendung (Web-App)

Die Web-App unter <https://fablab-ansbach.github.io/zeitschaetzspiel/> im Browser öffnen und auf **Arduino verbinden**
klicken. Im Auswahldialog den seriellen Port des Arduino wählen (z.B. ``/dev/ttyACM0`` oder ``COM3``).

Der Arduino startet beim Verbinden automatisch neu, der Status wechselt deshalb erst nach ein paar Sekunden auf
*Spiel bereit*. Ist der Port einmal freigegeben, verbindet sich die Seite beim nächsten Laden von selbst — praktisch
für den Kiosk-Betrieb.

Danach wie gewohnt: **Neues Spiel starten**, erster Tastendruck startet die Messung, zweiter stoppt sie.

Die Rangliste liegt im ``localStorage`` des Browsers, also pro Rechner und Browserprofil getrennt. Einzelne Einträge
lassen sich über das ``✕`` in der Zeile löschen, die komplette Liste über **Zurücksetzen**.

### Lokale Entwicklung

``` BASH
cd web
npm install
npm run dev      # Entwicklungsserver auf http://localhost:5173
npm run check    # Selbsttest der Ranglisten-Logik
npm run build    # Produktionsbuild nach web/dist
```

Die Audiodateien werden direkt aus ``resources/`` ausgeliefert (``publicDir`` in ``web/vite.config.ts``).

### Veröffentlichen

Entwickelt wird auf ``master``, veröffentlicht wird über den Release-Branch ``web``:

``` BASH
./publish.sh
```

Das Script prüft, dass das Arbeitsverzeichnis sauber ist, lässt ``npm run check`` und ``npm run build``
lokal durchlaufen – damit nichts Kaputtes auf dem Release-Branch landet – und schiebt den aktuellen Branch
dann auf ``web``. Der Workflow ``.github/workflows/pages.yml`` baut von dort und deployt nach GitHub Pages.

Einmalig in den Repo-Einstellungen unter **Settings → Pages** als Source **GitHub Actions** auswählen.
Ein Deploy lässt sich außerdem jederzeit manuell über **Actions → Deploy web app to GitHub Pages → Run workflow**
anstoßen.

## Verwendung (Python Frontend)

Das Frontent wird mit ``python3 game.py`` gestartet.
Nach dem öffnen der Oberfläche muss der Arduino verbunden werden. Dazu im Menü **Verbindung -> Verbinden** benutzen und den entsprechenden Seriellen Port angeben.

Nach erfolgreichem Verbindungsaufbau kann über den Button **Neues Spiel starten** ein Spiel gestartet werden.

Es wird vom Arduino eine zufällige ganzzahlige Zeit zwischen 5 und 30 Sekunden vorgegeben und als Zielzeit angezeigt.\
Mit dem ersten Tastendruck wird die Zeitmessung gestartet und durch eine Tonausgabe signalisiert.\
Beim zweiten Tastendruck wird die Zeitmessung gestoppt und sowohl die geschätzte Zeit, als auch die Abweichung in Sekunden angezeigt.

Möchte sich der Spieler in die Rangliste aufnehmen lassen, besteht nun die Möglichkeit einen Namen einzutragen und den Messwert in die Rangliste zu speichern.

Ist der eingegebene Namen bereits in der Rangliste enthalten bietet das Programm zwei Möglichkeiten an:

1. Namen beibehalten und alten Datensatz überschreiben
2. Neuen Namen eingeben und neuen Datensatz speichern

Soll das Spielergebnis nicht in die Rangliste aufgenommen werden, kann direkt ein neues Spiel gestartet werden.

## Rangliste

In der Oberfläche werden immer die 20 besten Messungen mit Namen, Zielzeit, Sollzeit und Abweichung angezeigt.

Maßgeblich für die Sortierung ist die relative Abweichung zwischen Sollzeit und gemessener Zeit, damit eine kurze und
eine lange Zielzeit vergleichbar bleiben.

Das Python Frontend speichert die Rangliste in der Datei leaderboard.json im Verzeichnis des Spiels; dort werden alle
Messungen über den Menüpunkt **Datei -> Rangliste zurücksetzen** entfernt. Die Web-App speichert sie stattdessen im
``localStorage`` des Browsers.

## Lizenzinformationen

Die Verwendeten Sounddateien stammen von pixybay.com und stehen zur kostenlosen Nutzung unter der [Pixabay-Inhaltslizenz](https://pixabay.com/de/service/license-summary/) zur Verfügung.
