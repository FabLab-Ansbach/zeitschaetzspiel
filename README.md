# Zeitschätzspiel

Es handelt sich um ein einfaches Zeitschätzspiel, bei dem eine vorgegebene Zeit möglichst genau abgeschätzt werden muss.\
Zur Zeitmessung und Auswertung der Eingaben wird ein Arduino verwendet. Die grafische Darstellung und die Verwaltung der
Spielergebnisse erfolgt mit einem Python Programm. Die Kommunikation zwischen Arduino und GUI erfolgt textbasiert über
eine Serielle Schnittstelle.

## Benötigtes Material

- Arduino mit USB-Schnittstelle
- Taster (z.B. Grobhandtaster)

## Hardwareaufbau

Der Hardwareaufbau ist denkbar einfach. Dazu wird der verwendete Taster mit GND und Pin2 am Arduino verbunden.\
Es wird kein zusätzlicher Pull-Up Widerstand benötigt, da der interne Pull-Up Widerstand vom Arduino verwendet wird.

## Abhängigkeiten

### Arduino Sketch

Der Arduino Sketch greift ausschließlich auf Systemfunktionen zu und benötigt keine zusätzlichen Librarys.

### Python Frontend

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

## Verwendung

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

In der Oberfläche werden immer die 20 besten Messungen mit Namen, Zielzeit, Sollzeit und Abweichung angezeigt. Maßgeblich für die Sortierung ist die Abweichung zwischen Sollzeit und gemessener Zeit.

Die Rangliste wird in der Datei leaderboard.json im Verzeichnis des Spiels gespeichert und beim nächsten Start des Programms automatisch wieder geladen.

Über den Menüpunkt **Datei -> Rangliste zurücksetzen** werden alle Messungen aus der Rangliste entfernt.

## Lizenzinformationen

Die Verwendeten Sounddateien stammen von pixybay.com und stehen zur kostenlosen Nutzung unter der [Pixabay-Inhaltslizenz](https://pixabay.com/de/service/license-summary/) zur Verfügung.
