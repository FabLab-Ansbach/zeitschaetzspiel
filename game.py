import serial
import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import os
import threading
import time
import serial.tools.list_ports
import pygame

class TimeGuessGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Zeit-Schätz-Spiel")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Serielle Verbindung
        self.serial_port = None
        self.connected = False
        self.serial_thread = None

        # Spielstatus
        self.game_active = False
        self.current_game = None

        # Rangliste
        self.leaderboard = []
        self.load_leaderboard()

        # UI-Elemente
        self.canvas_frame_id = None
        self.create_ui()

        pygame.mixer.init()

        # Verbindung nicht automatisch beim Start herstellen
        # Serielle Kommunikation wird in setup_connection gestartet

        # Protokoll für das Schließen des Fensters
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_ui(self):
        # ... (Restlicher Code von create_ui bleibt gleich bis zum Ranglisten-Teil) ...

        # Frame für Spielstatus
        status_frame = tk.Frame(self.root, padx=10, pady=10)
        status_frame.pack(fill=tk.X)

        self.status_label = tk.Label(status_frame, text="Spiel bereit", font=("Arial", 16))
        self.status_label.pack(side=tk.LEFT)

        self.connection_label = tk.Label(status_frame, text="Nicht verbunden", fg="red", font=("Arial", 12))
        self.connection_label.pack(side=tk.RIGHT)

        # Frame für Spielsteuerung
        control_frame = tk.Frame(self.root, padx=10, pady=5)
        control_frame.pack(fill=tk.X)

        self.start_button = tk.Button(control_frame, text="Neues Spiel starten",
                                      command=self.start_new_game, font=("Arial", 14),
                                      bg="#4CAF50", fg="white", padx=10, pady=5,
                                      state=tk.DISABLED)  # Standardmäßig deaktiviert bis Verbindung steht
        self.start_button.pack(pady=10)

        # Frame für Spielinformationen
        game_frame = tk.Frame(self.root, padx=10, pady=10, bg="#f0f0f0")
        game_frame.pack(fill=tk.X)

        self.target_time_label = tk.Label(game_frame, text="Zielzeit: -",
                                         font=("Arial", 24), bg="#f0f0f0")
        self.target_time_label.pack(pady=5)

        self.instruction_label = tk.Label(game_frame,
                                         text="Verbinde dich zuerst mit dem Arduino über das Menü.",
                                         font=("Arial", 12), bg="#f0f0f0")
        self.instruction_label.pack(pady=5)

        self.elapsed_time_label = tk.Label(game_frame, text="Deine Zeit: -",
                                          font=("Arial", 22), bg="#f0f0f0")
        self.elapsed_time_label.pack(pady=5)

        self.deviation_label = tk.Label(game_frame, text="Abweichung: -",
                                       font=("Arial", 22), bg="#f0f0f0")
        self.deviation_label.pack(pady=5)

        # Frame für Spielername
        name_frame = tk.Frame(self.root, padx=10, pady=10)
        name_frame.pack(fill=tk.X)

        self.name_label = tk.Label(name_frame, text="Spielername:", font=("Arial", 12))
        self.name_label.pack(side=tk.LEFT)

        self.name_entry = tk.Entry(name_frame, font=("Arial", 12), width=20)
        self.name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)  # Nimmt verfügbaren Platz ein
        self.name_entry.bind("<Return>", lambda event: self.submit_score())

        button_frame = tk.Frame(name_frame)
        button_frame.pack(side=tk.LEFT)

        self.submit_button = tk.Button(button_frame, text="Zur Rangliste hinzufügen",
                                       command=self.submit_score, state=tk.DISABLED,
                                       bg="#2196F3", fg="white")
        self.submit_button.pack(side=tk.LEFT, padx=5)

        self.skip_button = tk.Button(button_frame, text="Überspringen",
                                     command=self.skip_score, state=tk.DISABLED,
                                     bg="#9E9E9E", fg="white")
        self.skip_button.pack(side=tk.LEFT, padx=5)

        # --- Frame für Rangliste (Container) ---
        leaderboard_outer_frame = tk.Frame(self.root, padx=10, pady=10)
        leaderboard_outer_frame.pack(fill=tk.BOTH, expand=True)  # Füllt restlichen Platz

        tk.Label(leaderboard_outer_frame, text="Rangliste", font=("Arial", 16, "bold")).pack()

        # --- Canvas und Scrollbar für die Rangliste ---
        self.leaderboard_canvas = tk.Canvas(leaderboard_outer_frame)
        self.leaderboard_scrollbar = tk.Scrollbar(leaderboard_outer_frame, orient=tk.VERTICAL,
                                                  command=self.leaderboard_canvas.yview)
        self.scrollable_leaderboard_frame = tk.Frame(self.leaderboard_canvas)  # Frame *innerhalb* des Canvas

        # --- Änderung 1: ID speichern und Bindung an Canvas ---
        # Das Frame in den Canvas einbetten und die ID speichern
        self.canvas_frame_id = self.leaderboard_canvas.create_window(
            (0, 0),
            window=self.scrollable_leaderboard_frame,
            anchor="nw"  # Wichtig: Anker oben links
        )

        # Konfigurations-Event an den *Canvas* binden, um die Breite des Frames anzupassen
        self.leaderboard_canvas.bind("<Configure>", self._on_canvas_configure)
        # --- Ende Änderung 1 ---

        self.leaderboard_canvas.configure(yscrollcommand=self.leaderboard_scrollbar.set)

        self.leaderboard_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.leaderboard_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # --- Ende Canvas/Scrollbar ---

        # Initiales Anzeigen der (leeren) Rangliste
        self.update_leaderboard_display()

        # Menü
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Rangliste zurücksetzen", command=self.reset_leaderboard)
        file_menu.add_command(label="Beenden", command=self.on_closing)  # Geändert zu on_closing

        connection_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Verbindung", menu=connection_menu)
        connection_menu.add_command(label="Verbinden", command=self.setup_connection)
        connection_menu.add_command(label="Trennen", command=self.disconnect_serial)  # Trennen Option

    # --- Änderung 2: Neue Methode zum Anpassen der Frame-Breite ---
    def _on_canvas_configure(self, event):
        """Passt die Breite des Frames im Canvas an die Canvas-Breite an."""
        canvas_width = event.width
        # Setzt die Breite des *Fenster-Elements* im Canvas, das den Frame enthält
        self.leaderboard_canvas.itemconfig(self.canvas_frame_id, width=canvas_width)
        # Aktualisiere die Scrollregion, nachdem die Breite angepasst wurde
        # Notwendig, damit die Scrollbar weiß, wie groß der Inhalt ist
        self.leaderboard_canvas.configure(scrollregion=self.leaderboard_canvas.bbox("all"))
    # --- Ende Änderung 2 ---

    def update_leaderboard_display(self):
        # Bestehende Einträge im scrollbaren Frame löschen
        for widget in self.scrollable_leaderboard_frame.winfo_children():
            widget.destroy()

        # --- Spaltenkonfiguration mit Gewichten für dynamische Breite ---
        # Definieren Sie die relativen Breiten (Gewichte) der Spalten
        column_weights = [1, 5, 3, 3, 3, 3]  # Name etwas breiter gemacht
        headers = ["Rang", "Name", "Zielzeit (s)", "Gemessene Zeit (s)", "Abweichung (s)", "Abweichung (%)"]

        # Konfiguriere die Spalten im scrollable_leaderboard_frame, damit sie sich anpassen
        # Wichtig: Dies wirkt sich nur aus, wenn scrollable_leaderboard_frame
        #          die Breite hat, um die Gewichte anzuwenden (daher _on_canvas_configure)
        for i, weight in enumerate(column_weights):
            self.scrollable_leaderboard_frame.columnconfigure(i, weight=weight, uniform='leaderboard')  # 'uniform' kann helfen

        # --- Kopfzeile erstellen mit grid ---
        for i, header in enumerate(headers):
            lbl = tk.Label(self.scrollable_leaderboard_frame, text=header,
                           font=("Arial", 11, "bold"), relief=tk.RIDGE, padx=5, pady=2, bd=1)  # Etwas kleiner, mit Rand
            lbl.grid(row=0, column=i, sticky='nsew')  # nsew füllt Zelle komplett

        # --- Einträge in die Rangliste einfügen mit grid ---
        # Sortiere die Rangliste nach relativer Abweichung (aufsteigend)
        sorted_leaderboard = sorted(self.leaderboard, key=lambda x: (abs(x['deviation']) / x['target_time']) * 100 if x['target_time'] else float('inf'))

        for i, entry in enumerate(sorted_leaderboard):
            row_num = i + 1

            bg_color = "#f0f0f0" if i % 2 == 0 else "#ffffff"

            # Zellen erstellen und platzieren
            data_font = ("Arial", 10)  # Kleinere Schrift für Daten

            # Rang
            lbl_rank = tk.Label(self.scrollable_leaderboard_frame, text=str(i + 1), bg=bg_color, padx=5, pady=2,
                                font=data_font)
            lbl_rank.grid(row=row_num, column=0, sticky='nsew')

            # Name
            lbl_name = tk.Label(self.scrollable_leaderboard_frame, text=entry['name'], bg=bg_color, anchor='w', padx=5,
                                pady=2, font=data_font)
            lbl_name.grid(row=row_num, column=1, sticky='nsew')

            # Zielzeit
            lbl_target = tk.Label(self.scrollable_leaderboard_frame, text=f"{entry['target_time'] / 1000:.3f}",
                                  bg=bg_color, padx=5, pady=2, font=data_font)
            lbl_target.grid(row=row_num, column=2, sticky='nsew')

            # Gemessene Zeit
            lbl_elapsed = tk.Label(self.scrollable_leaderboard_frame, text=f"{entry['elapsed_time'] / 1000:.3f}",
                                   bg=bg_color, padx=5, pady=2, font=data_font)
            lbl_elapsed.grid(row=row_num, column=3, sticky='nsew')

            # Abweichung
            deviation = abs(entry['deviation'] / 1000)
            color = "green" if deviation < 0.5 else "orange" if deviation < 1.0 else "red"
            lbl_dev = tk.Label(self.scrollable_leaderboard_frame, text=f"{deviation:.3f}", fg=color, bg=bg_color,
                                padx=5, pady=2, font=data_font)
            lbl_dev.grid(row=row_num, column=4, sticky='nsew')

            # Relative Abweichung in Prozent
            relative_deviation = (abs(entry['deviation']) / entry['target_time']) * 100 if entry['target_time'] else 0
            lbl_rel_dev = tk.Label(self.scrollable_leaderboard_frame, text=f"{relative_deviation:.2f}%", bg=bg_color,
                                    padx=5, pady=2, font=data_font)
            lbl_rel_dev.grid(row=row_num, column=5, sticky='nsew')

        # Wichtig: Nach dem Hinzufügen von Widgets und Konfigurieren der Spalten
        # muss der Canvas möglicherweise seine Scrollregion neu berechnen.
        # Dies geschieht jetzt in _on_canvas_configure. Ein initiales
        # Update hier schadet aber nicht.
        self.scrollable_leaderboard_frame.update_idletasks()
        self.leaderboard_canvas.configure(scrollregion=self.leaderboard_canvas.bbox("all"))

    # ... (Rest der Methoden: setup_connection, check_initial_connection, etc. bleiben unverändert) ...
    def setup_connection(self):
        if self.connected:
            messagebox.showinfo("Info", "Bereits verbunden.")
            return

        try:
            ports = list(serial.tools.list_ports.comports())
            if not ports:
                messagebox.showerror("Fehler", "Keine seriellen Ports gefunden!")
                return

            port_names = [p.device for p in ports]
            port_info = [f"{p.device} - {p.description}" for p in ports]  # Mehr Infos anzeigen

            if len(ports) == 1:
                selected_port_device = ports[0].device
                # Keine Nachfrage bei nur einem Port
            else:
                # Dialog zur Auswahl des Ports
                selected_port_str = simpledialog.askstring("Port auswählen",
                                                       f"Verfügbare Ports:\n" + "\n".join(port_info) + "\n\nBitte Port eingeben (z.B. COM3 oder /dev/ttyACM0):",
                                                       parent=self.root)
                if not selected_port_str:
                    return  # Benutzer hat abgebrochen

                # Prüfen, ob der eingegebene Port gültig ist
                if selected_port_str not in port_names:
                    messagebox.showerror("Fehler", f"Ungültiger Port: {selected_port_str}")
                    return
                selected_port_device = selected_port_str

            # Verbindung herstellen
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()

            self.serial_port = serial.Serial(selected_port_device, 9600, timeout=0.1)
            self.root.after(2000, self.check_initial_connection)  # Warte 2s und prüfe Verbindung

        except serial.SerialException as e:
            messagebox.showerror("Verbindungsfehler", f"Konnte Port {selected_port_device} nicht öffnen:\n{e}")
            self.connected = False
            self.connection_label.config(text="Nicht verbunden", fg="red")
            self.start_button.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Verbindungsfehler", str(e))
            self.connected = False
            self.connection_label.config(text="Nicht verbunden", fg="red")
            self.start_button.config(state=tk.DISABLED)

    def check_initial_connection(self):
        # Nach kurzer Wartezeit prüfen, ob der Arduino bereit ist
        # (Optional: Sende einen PING oder erwarte eine READY Nachricht)
        try:
            if self.serial_port and self.serial_port.is_open:
                # Optional: Warte auf eine "READY" Nachricht vom Arduino
                # self.serial_port.write(b"CHECK_READY\n") # Beispielbefehl
                # Oder gehe einfach davon aus, dass es geklappt hat
                self.connected = True
                self.connection_label.config(text=f"Verbunden mit {self.serial_port.port}", fg="green")
                self.start_button.config(state=tk.NORMAL)
                self.instruction_label.config(text="Drücke 'Neues Spiel starten' oder den Taster")  # Aktualisiert

                # Starte den Lese-Thread erst *nach* erfolgreicher Verbindung
                if self.serial_thread is None or not self.serial_thread.is_alive():
                    self.serial_thread = threading.Thread(target=self.read_serial, daemon=True)
                    self.serial_thread.start()

                messagebox.showinfo("Verbindung", f"Erfolgreich mit {self.serial_port.port} verbunden!")

            else:
                # Dieser Fall sollte eigentlich nicht eintreten, wenn Serial() erfolgreich war
                raise serial.SerialException("Port nicht mehr offen nach Wartezeit.")

        except Exception as e:
            port_name = self.serial_port.port if self.serial_port else "Unbekannt"
            messagebox.showerror("Verbindungsfehler", f"Keine Antwort vom Arduino auf {port_name}:\n{e}")
            self.disconnect_serial()  # Verbindung sauber trennen

    def disconnect_serial(self):
        """Trennt die serielle Verbindung sauber."""
        self.game_active = False  # Spiel stoppen, falls aktiv
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception as e:
                print(f"Fehler beim Schließen des Ports: {e}")
        self.serial_port = None
        self.connected = False  # Wichtig: Setze connected auf False
        # UI Updates im Hauptthread sicherstellen
        self.root.after(0, self._update_ui_disconnected)
        print("Serielle Verbindung getrennt.")
        # Der Lese-Thread beendet sich selbst, da self.connected False wird

    def _update_ui_disconnected(self):
        """Aktualisiert die UI-Elemente nach dem Trennen der Verbindung."""
        self.connection_label.config(text="Nicht verbunden", fg="red")
        self.start_button.config(state=tk.DISABLED)
        self.status_label.config(text="Verbindung getrennt")
        self.instruction_label.config(text="Verbinde dich zuerst mit dem Arduino über das Menü.")
        # Reset game info labels
        self.target_time_label.config(text="Zielzeit: -")
        self.elapsed_time_label.config(text="Deine Zeit: -")
        self.deviation_label.config(text="Abweichung: -", fg='black')
        self.submit_button.config(state=tk.DISABLED)
        self.skip_button.config(state=tk.DISABLED)

    def start_new_game(self):
        if not self.connected or not self.serial_port or not self.serial_port.is_open:
            messagebox.showerror("Fehler", "Keine Verbindung zum Arduino!", parent=self.root)
            return

        try:
            # Starte ein neues Spiel
            print("Sende START_GAME an Arduino")
            self.serial_port.write(b"START_GAME\n")
            self.serial_port.flush()  # Sicherstellen, dass Daten gesendet werden
            self.game_active = True

            # UI zurücksetzen
            self.target_time_label.config(text="Warte auf Zielzeit...")
            self.elapsed_time_label.config(text="Deine Zeit: -")
            self.deviation_label.config(text="Abweichung: -")
            self.status_label.config(text="Spiel wird vorbereitet...")
            self.instruction_label.config(text="Warte auf Spielstart...")
            self.deviation_label.config(fg="black")  # Farbe zurücksetzen

            # Deaktiviere Start-Button während des Spiels
            self.start_button.config(state=tk.DISABLED)

            # Deaktiviere Eingabefelder für Score
            self.submit_button.config(state=tk.DISABLED)
            self.skip_button.config(state=tk.DISABLED)
            self.name_entry.delete(0, tk.END)

        except serial.SerialException as e:
            messagebox.showerror("Kommunikationsfehler",
                                 f"Fehler beim Senden an Arduino:\n{e}\nVerbindung wird getrennt.", parent=self.root)
            self.disconnect_serial()  # Bei Sendefehler Verbindung trennen
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Starten des Spiels: {e}", parent=self.root)
            self.game_active = False
            # Nur wenn noch verbunden, Start-Button wieder aktivieren
            if self.connected:
                self.start_button.config(state=tk.NORMAL)

    def read_serial(self):
        print("Serial Read-Thread gestartet.")
        buffer = ""
        while self.connected:  # Schleife läuft nur solange connected=True
            if self.serial_port and self.serial_port.is_open:
                try:
                    # Daten lesen, wenn verfügbar
                    if self.serial_port.in_waiting > 0:
                        # Lese Bytes und füge sie zum Puffer hinzu
                        data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
                        buffer += data

                        # Verarbeite vollständige Zeilen im Puffer
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()  # Entferne Leerzeichen und ggf. \r
                            if line:
                                print(f"Arduino: {line}")  # Debug-Ausgabe
                                # Stelle sicher, dass UI-Updates im Hauptthread laufen
                                self.root.after(0, self.process_arduino_message, line)

                except serial.SerialException as e:
                    print(f"Serieller Fehler im Lesethread: {e}")
                    # Bei Lesefehler Verbindung als verloren markieren
                    # Stelle sicher, dass dies im Hauptthread passiert
                    if self.connected:  # Nur wenn wir dachten, wir wären verbunden
                        self.root.after(0, self.handle_connection_loss)
                    break  # Thread beenden
                except Exception as e:
                    # Verhindert Absturz bei unerwarteten Dekodierungsfehlern etc.
                    print(f"Allgemeiner Fehler im Lesethread: {e}")
                    # Optional: Hier auch Verbindung trennen?
                    time.sleep(0.1)  # Kurze Pause bei unerwartetem Fehler
            else:
                # Wenn Port nicht mehr offen ist oder None, Thread beenden
                print("Port nicht mehr offen oder nicht vorhanden. Read-Thread wird beendet.")
                break  # Beendet die while self.connected Schleife

            time.sleep(0.05)  # Kurze Pause, um CPU zu schonen

        print("Serial Read-Thread beendet.")

    def handle_connection_loss(self):
        """Wird aufgerufen, wenn ein serieller Fehler auftritt (im Hauptthread)."""
        if self.connected:  # Nur handeln, wenn wir dachten, wir wären verbunden
            # Verhindert mehrere Fehlermeldungen bei schnellen Fehlern
            self.connected = False  # Sofort auf False setzen
            messagebox.showerror("Verbindungsfehler", "Verbindung zum Arduino verloren!", parent=self.root)
            self.disconnect_serial()  # Ruft UI-Updates etc. auf

    def process_arduino_message(self, message):
        # Diese Funktion wird jetzt über self.root.after() im Hauptthread aufgerufen
        if not self.connected and not message.startswith("PC_READY"):
            # Ignoriere Nachrichten nach Verbindungsverlust, außer PC_READY
            # PC_READY könnte von einem Neustart des Arduinos kommen
            print(f"Ignoriere Nachricht nach Verbindungsverlust: {message}")
            return

        try:
            if message.startswith("TARGET_TIME:"):
                target_time = int(message.split(":")[1].strip())
                self.current_game = {
                    'target_time': target_time,
                    'elapsed_time': 0,
                    'deviation': 0
                }
                self.target_time_label.config(text=f"Zielzeit: {target_time / 1000:.1f} Sekunden")
                self.status_label.config(text="Spiel läuft")  # Status hier anpassen
                self.instruction_label.config(text="Drücke Taster zum Starten...")  # Erste Anweisung nach Zielzeit

            elif message == "WAITING_FOR_BUTTON":
                self.instruction_label.config(
                    text="Drücke den Taster zum Starten der Zeitmessung")
                self.status_label.config(text="Bereit zum Start")  # Klarerer Status

            elif message == "TIME_STARTED":
                startsound = pygame.mixer.Sound("resources/audio/start.mp3") # Start-Sound setzen
                pygame.mixer.Sound.play(startsound) # Start-Sound abspielen

                self.status_label.config(text="Zeitmessung läuft...")
                self.instruction_label.config(
                    text="Drücke den Taster erneut zum Stoppen")  # Verkürzt

            elif message.startswith("ELAPSED_TIME:"):
                # Nur verarbeiten, wenn ein Spiel aktiv ist
                if self.current_game:
                    elapsed_time = int(message.split(":")[1].strip())
                    self.current_game['elapsed_time'] = elapsed_time
                    self.elapsed_time_label.config(
                        text=f"Deine Zeit: {elapsed_time / 1000:.3f} Sekunden")

            elif message.startswith("DEVIATION:"):
                # Nur verarbeiten, wenn ein Spiel aktiv ist
                if self.current_game:
                    deviation = int(message.split(":")[1].strip())
                    self.current_game['deviation'] = deviation
                    deviation_abs_sec = abs(deviation) / 1000

                # Relative Abweichung in Prozent berechnen
                target_time = self.current_game['target_time']
                if target_time > 0:
                    deviation_percent = (abs(deviation) / target_time) * 100
                    self.deviation_label.config(
                        text=f"Abweichung: {deviation_abs_sec:.3f} Sekunden ({deviation_percent:.1f}%)")
                else:
                    # Fallback, falls target_time 0 ist
                    self.deviation_label.config(
                        text=f"Abweichung: {deviation_abs_sec:.3f} Sekunden")

                    # Farbe der Abweichung je nach Genauigkeit anpassen
                    color = "green" if deviation_abs_sec < 0.5 else "orange" if deviation_abs_sec < 1.0 else "red"
                    self.deviation_label.config(fg=color)

                    # Sound-Ausgabe, je nach Zeitabweichung
                    if deviation_abs_sec >= 10:
                        fail = pygame.mixer.Sound("resources/audio/fail.mp3")
                        pygame.mixer.Sound.play(fail)
                    elif deviation_abs_sec == 0:
                        winner = pygame.mixer.Sound("resources/audio/winner.mp3")
                        pygame.mixer.Sound.play(winner)
                    else:
                        fail = pygame.mixer.Sound("resources/audio/good.mp3")
                        pygame.mixer.Sound.play(fail)

            elif message == "GAME_ENDED":
                self.game_active = False  # Wichtig: Spielstatus aktualisieren
                self.status_label.config(text="Spiel beendet")
                self.instruction_label.config(
                    text="Trage Namen ein oder starte neu")  # Verkürzt
                if self.connected:  # Nur aktivieren, wenn noch verbunden
                    self.start_button.config(state=tk.NORMAL)
                    self.submit_button.config(state=tk.NORMAL)  # Buttons aktivieren
                    self.skip_button.config(state=tk.NORMAL)
                else:
                    # Sicherstellen, dass Buttons deaktiviert bleiben, wenn keine Verbindung
                    self.submit_button.config(state=tk.DISABLED)
                    self.skip_button.config(state=tk.DISABLED)

            elif message == "PC_READY":  # Arduino meldet Bereitschaft nach Neustart/Init
                print("Arduino meldet PC_READY")
                # Wenn wir verbunden sind oder versuchen zu verbinden, UI aktualisieren
                if self.connected or (self.serial_port and self.serial_port.is_open):
                    self.status_label.config(text="Arduino bereit")
                    self.start_button.config(state=tk.NORMAL)
                    self.instruction_label.config(text="Drücke 'Neues Spiel starten'")
                else:
                    # Wenn keine Verbindung (mehr) besteht, nur loggen
                    print("PC_READY empfangen, aber nicht verbunden.")

            # Handle andere unerwartete Nachrichten (optional)
            # else:
            #    print(f"Unbekannte Nachricht vom Arduino: {message}")

        except ValueError as e:
            print(f"Fehler beim Konvertieren der Nachricht '{message}': {e}")
        except IndexError as e:
            print(f"Fehler beim Splitten der Nachricht '{message}': {e}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Unerwarteter Fehler bei der Nachrichtenverarbeitung: {e}")

    def submit_score(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Warnung", "Bitte gib einen Namen ein!", parent=self.root)
            return

        # Stelle sicher, dass Spieldaten vorhanden und gültig sind
        if self.current_game and 'target_time' in self.current_game and 'elapsed_time' in self.current_game and 'deviation' in self.current_game:
            # Prüfen, ob der Name bereits in der Rangliste vorhanden ist
            for i, entry in enumerate(self.leaderboard):
                if entry['name'] == name:
                    # Dialog anzeigen
                    answer = messagebox.askquestion("Name bereits vorhanden",
                                                    "Der Name ist bereits in der Rangliste vorhanden. Möchtest du ihn überschreiben?",
                                                    icon='warning', parent=self.root)
                    if answer == 'yes':
                        # Eintrag überschreiben
                        self.leaderboard[i] = {
                            'name': name,
                            'target_time': self.current_game['target_time'],
                            'elapsed_time': self.current_game['elapsed_time'],
                            'deviation': self.current_game['deviation']
                        }
                        self.leaderboard.sort(key=lambda x: abs(x['deviation']))
                        self.save_leaderboard()
                        self.update_leaderboard_display()

                        # UI aktualisieren und Buttons deaktivieren
                        self.name_entry.delete(0, tk.END)
                        self.submit_button.config(state=tk.DISABLED)
                        self.skip_button.config(state=tk.DISABLED)
                        self.status_label.config(text="Bereit für ein neues Spiel")
                        messagebox.showinfo("Rangliste", f"'{name}' wurde überschrieben!", parent=self.root)
                        return
                    else:
                        # Speichern abbrechen
                        return

            # Wenn der Name nicht vorhanden ist, neuen Eintrag hinzufügen
            entry = {
                'name': name,
                'target_time': self.current_game['target_time'],
                'elapsed_time': self.current_game['elapsed_time'],
                'deviation': self.current_game['deviation']
            }
            self.leaderboard.append(entry)
            self.leaderboard.sort(key=lambda x: abs(x['deviation']))
            # Nur Top N behalten (optional)
            # max_leaderboard_size = 20
            # if len(self.leaderboard) > max_leaderboard_size:
            #    self.leaderboard = self.leaderboard[:max_leaderboard_size]
            self.save_leaderboard()
            self.update_leaderboard_display()

            # UI aktualisieren und Buttons deaktivieren
            self.name_entry.delete(0, tk.END)
            self.submit_button.config(state=tk.DISABLED)
            self.skip_button.config(state=tk.DISABLED)
            self.status_label.config(text="Bereit für ein neues Spiel")
            messagebox.showinfo("Rangliste", f"'{name}' zur Rangliste hinzugefügt!", parent=self.root)
        else:
            messagebox.showerror("Fehler", "Keine gültigen Spieldaten zum Speichern vorhanden.\nBitte zuerst ein Spiel beenden.", parent=self.root)
            self.submit_button.config(state=tk.DISABLED)  # Sicherstellen, dass Button deaktiviert ist
            self.skip_button.config(state=tk.DISABLED)
    def skip_score(self):
        # UI zurücksetzen ohne Score zu speichern
        self.name_entry.delete(0, tk.END)
        self.submit_button.config(state=tk.DISABLED)
        self.skip_button.config(state=tk.DISABLED)
        self.status_label.config(text="Bereit für ein neues Spiel")
        # Die alten Spielwerte bleiben sichtbar, bis ein neues Spiel gestartet wird


    def load_leaderboard(self):
        leaderboard_file = "leaderboard.json"
        try:
            if os.path.exists(leaderboard_file):
                with open(leaderboard_file, "r", encoding='utf-8') as file:
                    try:
                        loaded_data = json.load(file)
                        # Validierung: Ist es eine Liste und enthalten die Elemente die nötigen Keys?
                        if isinstance(loaded_data, list):
                             self.leaderboard = [
                                 entry for entry in loaded_data
                                 if isinstance(entry, dict) and all(k in entry for k in ['name', 'target_time', 'elapsed_time', 'deviation'])
                             ]
                             # Sortieren nach dem Laden
                             self.leaderboard.sort(key=lambda x: abs(x.get('deviation', float('inf')))) # .get() für Robustheit
                        else:
                             print(f"Warnung: Inhalt von {leaderboard_file} ist keine Liste. Rangliste wird zurückgesetzt.")
                             self.leaderboard = []
                    except json.JSONDecodeError:
                         print(f"Fehler: {leaderboard_file} ist korrupt oder leer. Rangliste wird zurückgesetzt.")
                         self.leaderboard = []
                         # Optional: Backup erstellen oder Datei löschen/neu erstellen
                         # try:
                         #     os.rename(leaderboard_file, leaderboard_file + ".corrupt")
                         # except OSError:
                         #     pass
            else:
                 self.leaderboard = [] # Keine Datei vorhanden, starte mit leerer Liste
        except Exception as e:
            print(f"Allgemeiner Fehler beim Laden der Rangliste: {e}")
            self.leaderboard = []


    def save_leaderboard(self):
        leaderboard_file = "leaderboard.json"
        try:
            # Stelle sicher, dass wir eine Liste von Dictionaries speichern
            if isinstance(self.leaderboard, list):
                with open(leaderboard_file, "w", encoding='utf-8') as file:
                    json.dump(self.leaderboard, file, indent=4) # indent für bessere Lesbarkeit
            else:
                print("Fehler: Ranglistendaten sind keine Liste. Speichern abgebrochen.")
                messagebox.showerror("Speicherfehler", "Interner Fehler: Ranglistendaten sind korrupt.", parent=self.root)

        except TypeError as e:
             print(f"Fehler beim Serialisieren der Rangliste: {e}")
             messagebox.showerror("Speicherfehler", f"Fehler beim Konvertieren der Ranglistendaten:\n{e}", parent=self.root)
        except Exception as e:
            print(f"Allgemeiner Fehler beim Speichern der Rangliste: {e}")
            messagebox.showerror("Speicherfehler", f"Die Rangliste konnte nicht gespeichert werden:\n{e}", parent=self.root)


    def reset_leaderboard(self):
        if messagebox.askyesno("Rangliste zurücksetzen", "Möchtest du wirklich die gesamte Rangliste löschen?\nDiese Aktion kann nicht rückgängig gemacht werden.", parent=self.root, icon='warning'):
            self.leaderboard = []
            self.save_leaderboard() # Leere Liste speichern
            self.update_leaderboard_display() # Anzeige aktualisieren
            messagebox.showinfo("Rangliste", "Die Rangliste wurde zurückgesetzt!", parent=self.root)


    def on_closing(self):
        """Wird aufgerufen, wenn das Fenster geschlossen wird."""
        print("Schließe Anwendung...")
        # Trenne die Verbindung sauber, wenn sie besteht
        if self.connected:
             self.disconnect_serial()

        # Warten bis der Thread wirklich beendet ist (optional, aber sicherer)
        if self.serial_thread and self.serial_thread.is_alive():
             print("Warte auf Beendigung des Lese-Threads...")
             try:
                 # Gib dem Thread etwas Zeit zum Beenden nach dem Setzen von self.connected = False
                 self.serial_thread.join(timeout=0.5) # Warte max 0.5 Sekunden
                 if self.serial_thread.is_alive():
                     print("Warnung: Lese-Thread konnte nicht sauber beendet werden.")
             except Exception as e:
                 print(f"Fehler beim Warten auf Thread: {e}")

        print("Tkinter-Fenster wird zerstört.")
        self.root.destroy() # Tkinter-Fenster zerstören

if __name__ == "__main__":
    root = tk.Tk()
    game = TimeGuessGame(root)
    root.mainloop()