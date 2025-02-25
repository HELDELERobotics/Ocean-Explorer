#include <DallasTemperature.h>
#include <OneWire.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// Erstelle eine float Liste für Temperaturwerte
float dataList[1000];

int dataIndex = 0;
unsigned long startMillis = 0;

#define ONE_WIRE_BUS 23
#define RELAY_PIN 19  // Der Pin, an dem das Relais angeschlossen ist

// Definiere die UUIDs für den Service und die Charakteristik
#define SERVICE_UUID        "12345678-1234-1234-1234-123456789abc"
#define CHARACTERISTIC_UUID "87654321-4321-4321-4321-123456789abc"

OneWire oneWire(ONE_WIRE_BUS);

DallasTemperature sensors(&oneWire);

float temperatureC = 0.0;

BLECharacteristic *pCharacteristic;
bool deviceConnected = false;

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        Serial.println("Gerät verbunden!");
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        Serial.println("Gerät getrennt!");
        BLEAdvertising *pAdvertising = pServer->getAdvertising();
        pAdvertising->start();
        startMillis = millis(); // Timer zurücksetzen
    }
};

void setup() {
  Serial.begin(115200);

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW); // Relais initialisieren (ausgeschaltet)

  BLEDevice::init("ESP32_Relay");
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Erstelle einen Service mit der definierten UUID
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Erstelle eine Charakteristik mit der definierten UUID und den nötigen Eigenschaften
  pCharacteristic = pService->createCharacteristic(
                       CHARACTERISTIC_UUID,
                       BLECharacteristic::PROPERTY_READ |
                       BLECharacteristic::PROPERTY_WRITE
                   );

  pCharacteristic->setValue("OFF"); // Initialwert des Relais

  // Füge Descriptor hinzu, um Benachrichtigungen zu ermöglichen
  pCharacteristic->addDescriptor(new BLE2902());

  pService->start();

  BLEAdvertising *pAdvertising = pServer->getAdvertising();
  pAdvertising->start();

  sensors.begin();
  if (!sensors.getDeviceCount()) {
    Serial.println("Kein DS18B20-Sensor gefunden!");
  }

  Serial.println("ESP32 bereit für die Verbindung...");
  startMillis = millis();
}

void measureTemperature() {
  // Fordere den Sensor auf, die Temperatur zu messen
  sensors.requestTemperatures();

  // Lese die Temperatur des ersten Sensors
  float temperature = sensors.getTempCByIndex(0);

  // Gebe die Temperatur aus
  Serial.print("Temperatur: ");
  Serial.print(temperature);
  Serial.println(" °C");

  // Füge die Temperatur in das Array dataList ein
  if (dataIndex < sizeof(dataList) / sizeof(dataList[0])) {
    dataList[dataIndex] = temperature;
    dataIndex++;
  } else {
    // Array zurücksetzen, wenn es voll ist
    dataIndex = 0;
    dataList[dataIndex] = temperature;
    dataIndex++;
  }
  delay(1000);
}

void processCommands() {
  String command = pCharacteristic->getValue().c_str();

  if (command == "/open valve") {
    digitalWrite(RELAY_PIN, HIGH);  // Relais einschalten
    Serial.println("Relais eingeschaltet!");
  } else if (command == "/close valve") {
    digitalWrite(RELAY_PIN, LOW);  // Relais ausschalten
    Serial.println("Relais ausgeschaltet!");
  } else if (command == "/get data temperature") {
    // Simulierte Temperaturdaten
    String data = "";

    // Stelle sicher, dass die Daten korrekt zusammengefügt werden
    for (int i = 0; i < dataIndex; i++) {
      data += String(dataList[i], 2);  // Temperaturwerte als String (mit 2 Dezimalstellen)
      if (i < dataIndex - 1) {
        data += ",";  // Komma hinzufügen, wenn es nicht der letzte Wert ist
      }
    }

    // Debugging-Ausgabe
    Serial.println("Daten zum Senden:");
    Serial.println(data);  // Ausgabe in der Konsole

    // Setze den Wert der BLE-Charakteristik mit den tatsächlichen Daten
    pCharacteristic->setValue(data.c_str());  // Konvertiere in C-String
    delay(1000);
    pCharacteristic->notify();  // Benachrichtige den Client
  }
}

void loop() {
  if (!deviceConnected) {
    measureTemperature();
    unsigned long elapsedMillis = millis() - startMillis;
    Serial.print("Vergangene Zeit: ");
    Serial.print(elapsedMillis / 1000);
    Serial.println(" Sekunden");
    
    if (elapsedMillis >= 300000) { // 5 Minuten vergangen
      digitalWrite(RELAY_PIN, HIGH);  // Relais einschalten
      Serial.println("Relais nach 5 Minuten eingeschaltet!");
    }
  } else {
    startMillis = millis(); // Timer zurücksetzen, wenn verbunden
    processCommands();
  }
}