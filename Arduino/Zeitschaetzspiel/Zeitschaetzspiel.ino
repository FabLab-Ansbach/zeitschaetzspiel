const int buttonPin = 2;  // Taster an Pin 2
unsigned long randomTime;  // Zufällige Zeit in Millisekunden
unsigned long startTime;   // Startzeit
unsigned long elapsedTime; // Verstrichene Zeit
bool timing = false;       // Zeitmessung aktiv?
bool gameReady = false;    // Spiel bereit?
bool waitingForStart = false; // Warten auf ersten Tastendruck zum Starten der Zeitmessung

// Buffer für eingehende Befehle
char inputBuffer[20];
int bufferIndex = 0;

void setup() {
  pinMode(buttonPin, INPUT_PULLUP);  // Taster mit Pull-up-Widerstand
  Serial.begin(9600);                // Serielle Kommunikation starten
  randomSeed(analogRead(0));         // Zufallsgenerator initialisieren
  
  delay(1000);  // Kurze Pause
  
  Serial.println("Zeit-Schätz-Spiel bereit!");
  Serial.println("PC_READY");        // Signal an PC senden
  Serial.println("Sende 'START_GAME' um das Spiel zu starten");
}

void loop() {

  // Serielle Eingabe verarbeiten
  if (Serial.available() > 0) {
    char inChar = Serial.read();
    
    // Debug-Ausgabe für jedes empfangene Zeichen
    Serial.print("Zeichen empfangen: ");
    Serial.print(inChar);
    Serial.print(" (ASCII: ");
    Serial.print((int)inChar);
    Serial.println(")");
    
    // Zeilenumbruch oder Carriage Return erkennen
    if (inChar == '\n' || inChar == '\r') {
      // String beenden
      inputBuffer[bufferIndex] = '\0';
      
      // Debug-Ausgabe des vollständigen Befehls
      Serial.print("Vollständiger Befehl: ");
      Serial.println(inputBuffer);
      
      // Befehl verarbeiten
      if (strcmp(inputBuffer, "START_GAME") == 0) {
        // Neues Spiel vom PC starten
        randomTime = random(5, 31) * 1000;  // 5-30 Sekunden in ms
        
        Serial.print("Zufällige Zeit generiert: ");
        Serial.println(randomTime);
        
        Serial.print("TARGET_TIME:");
        Serial.println(randomTime);
        
        waitingForStart = true;  // Warten auf Tastendruck zum Starten der Zeitmessung
        gameReady = true;        // Spiel ist bereit
        timing = false;          // Zeitmessung noch nicht aktiv
        
        Serial.println("WAITING_FOR_BUTTON"); // Signal an PC senden
      }
      
      // Buffer zurücksetzen
      bufferIndex = 0;
    } 
    // Normales Zeichen zum Buffer hinzufügen
    else if (bufferIndex < sizeof(inputBuffer) - 1) {
      inputBuffer[bufferIndex++] = inChar;
    }
  }

  // Auf Tastendruck warten (LOW = gedrückt wegen Pull-up)
  if (digitalRead(buttonPin) == LOW) {
    delay(50);  // Entprellung
    
    // Warten bis Taste losgelassen wird
    while (digitalRead(buttonPin) == LOW) {
      delay(10);
    }
    
    if (gameReady && waitingForStart) {
      // Zeitmessung starten (erster Tastendruck)
      Serial.println("TIME_STARTED");
      
      startTime = millis();  // Startzeit speichern
      timing = true;         // Zeitmessung aktivieren
      waitingForStart = false; // Nicht mehr auf Startdruck warten
    }
    else if (timing) {
      // Spiel beenden, Zeit messen (zweiter Tastendruck)
      elapsedTime = millis() - startTime;
      timing = false;
      
      // Ergebnis senden
      Serial.print("ELAPSED_TIME:");
      Serial.println(elapsedTime);
      
      // Abweichung berechnen
      long deviation = elapsedTime - randomTime;
      Serial.print("DEVIATION:");
      Serial.println(deviation);
      
      // Spiel zurücksetzen
      gameReady = false;
      
      // Signalisieren, dass das Spiel beendet ist
      Serial.println("GAME_ENDED");
    }
  }
}
