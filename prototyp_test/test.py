import asyncio
from bleak import BleakClient, BleakError
from colorama import init, Fore
import pandas as pd  # Für Excel-Ausgabe

# Initialisiere colorama
init(autoreset=True)

# MAC-Adresse des ESP32
esp32_mac_address = "A0:B7:65:24:BB:F6"  # Ersetze dies mit der MAC-Adresse deines ESP32

# Service- und Charakteristik-UUIDs (müssen mit den ESP32-UUIDs übereinstimmen)
SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"
CHARACTERISTIC_UUID = "87654321-4321-4321-4321-123456789abc"

# Status des Testmodus
testmode = False

# Liste zur Speicherung der Temperaturdaten
temperature_data_list = []

# Funktion zum Speichern der Temperaturdaten als Excel-Datei
def save_to_excel(data_type):
    try:
        if data_type == "temperature":
            # Umwandlung der Liste in ein DataFrame, aber jetzt jeden Wert in einer eigenen Zelle (Spalte)
            df = pd.DataFrame(temperature_data_list, columns=["Temperatur"])
            output_file = f"{data_type}_data.xlsx"
            df.to_excel(output_file, index=False)  # Ohne Index speichern
            print(Fore.GREEN + f"{data_type.capitalize()}-Daten erfolgreich in '{output_file}' gespeichert.")
        else:
            print(Fore.RED + f"Datentyp '{data_type}' wird nicht unterstützt.")
    except Exception as e:
        print(Fore.RED + f"Fehler beim Speichern der Excel-Datei: {e}")

# Funktion zum Senden von Befehlen
async def send_command(client, command):
    try:
        print(Fore.GREEN + f"Sending command: {command}")
        await client.write_gatt_char(CHARACTERISTIC_UUID, command.encode())
        print(Fore.GREEN + f"Command '{command}' sent!")
    except BleakError as e:
        print(Fore.RED + f"Error in BLE communication: {e}")
    except Exception as e:
        print(Fore.RED + f"Unknown error: {e}")

# Funktion zum Abrufen von Daten
async def get_data(client, command):
    try:
        # Sende den Befehl an den ESP32
        await send_command(client, "/get data " + command)

        if command == "temperature":
            # Lese die Antwort vom ESP32
            value = await client.read_gatt_char(CHARACTERISTIC_UUID)
            received_data = value.decode("utf-8").strip()  # Entferne führende/nachfolgende Leerzeichen
            
            # Wenn die Antwort nicht der Befehl ist, sondern die tatsächlichen Daten
            if not received_data.startswith("/get data"):
                print(Fore.GREEN + f"Empfangene Daten: {received_data}")
                
                # Aufteilen der empfangenen Daten, indem wir bei Kommas oder Leerzeichen trennen
                temperature_values = received_data.split(",")  # Annahme: Temperaturwerte sind durch Kommas getrennt

                # Entferne Leerzeichen und speichere die Werte als Liste in einer neuen Zeile
                for temp in temperature_values:
                    # Entfernen von Leerzeichen, um sicherzustellen, dass die Werte sauber sind
                    temp_value = temp.strip()
                    if temp_value:  # Sicherstellen, dass der Wert nicht leer ist
                        temperature_data_list.append([temp_value])  # Jeden Wert als Liste in einer neuen Zeile
                print(Fore.CYAN + f"Aktualisierte Temperaturdatenliste: {temperature_data_list}")
            else:
                print(Fore.RED + "Befehl wurde als Antwort empfangen, keine echten Daten.")
        else:
            print(Fore.RED + f"Unknown data command: {command}")
    except BleakError as e:
        print(Fore.RED + f"Error while fetching data: {e}")
    except Exception as e:
        print(Fore.RED + f"Unknown error: {e}")

# Hilfsfunktion zur Anzeige von Befehlen
def show_help():
    print(Fore.MAGENTA + "\n" + "="*50)
    print(Fore.MAGENTA + " Available Commands ".center(50, "="))
    print("="*50)
    print(Fore.CYAN + "/get data temperature   - Fetches the temperature data.")
    print(Fore.CYAN + "/save \"temperature\" to excel - Saves the temperature data to an Excel file.")
    print(Fore.CYAN + "/help                   - Displays this help.")
    print(Fore.CYAN + "/quit                   - Exits the program.")
    print(Fore.CYAN + "/help testmode          - Displays help for testmode commands.")
    print("="*50 + "\n")

def show_testmode_help():
    print(Fore.MAGENTA + "\n" + "="*50)
    print(Fore.MAGENTA + " Testmode Commands ".center(50, "="))
    print("="*50)
    print(Fore.CYAN + "/activate testmode   - Activates the testmode.")
    print(Fore.CYAN + "/deactivate testmode  - Deactivates the testmode.")
    print(Fore.CYAN + "/open valve        - Activates the valve (only in testmode).")
    print(Fore.CYAN + "/close valve       - Deactivates the valve (only in testmode).")
    print("="*50 + "\n")

# ASCII-Logo mit "Ocean Explorer"
def show_logo():
    logo = """
     OOO   CCCC  EEEEE N   N    EEEEE X   X  PPPP  L      OOO  RRRR   EEEEE RRRR
    O   O C      E     NN  N    E      X X   P   P L     O   O R   R  E     R   R
    O   O C      EEEE  N N N    EEEE    X    PPPP  L     O   O RRRR   EEEE  RRRR
    O   O C      E     N  NN    E      X X   P     L     O   O R  R   E     R  R
     OOO   CCCC  EEEEE N   N    EEEEE X   X  P     LLLLL  OOO  R   R  EEEEE R   R
    """
    print(Fore.BLUE + logo)

# Hauptfunktion
async def main():
    global testmode  # Zugriff auf die globale Variable für den Testmodus

    try:
        async with BleakClient(esp32_mac_address) as client:
            if client.is_connected:
                # Zeige Logo und Header
                show_logo()
                print(Fore.GREEN + "="*50)
                print(Fore.GREEN + " Connected to ESP32 ".center(50, "="))
                print("="*50)

                # Kommando-Loop
                while True:
                    print(Fore.YELLOW + "\n" + "-"*50)
                    command = input(Fore.WHITE + "Enter a command: ").strip().lower()

                    if command == "/quit":
                        print(Fore.RED + "Disconnecting and exiting the program.")
                        break
                    elif command == "/activate testmode":
                        testmode = True
                        print(Fore.GREEN + "Testmode activated.")
                    elif command == "/deactivate testmode":
                        testmode = False
                        print(Fore.GREEN + "Testmode deactivated.")
                    elif command == "/open valve" or command == "/close valve":
                        if testmode:
                            await send_command(client, command)
                        else:
                            print(Fore.RED + "Testmode must be activated to use this command.")
                    elif command.startswith("/get data"):
                        data_command = command[len("/get data "):].strip()
                        await get_data(client, data_command)
                    elif command.startswith("/save") and "to excel" in command:
                        data_type = command.split(" ")[1].strip("\"")
                        save_to_excel(data_type)
                    elif command == "/help":
                        show_help()
                    elif command == "/help testmode":
                        show_testmode_help()
                    else:
                        print(Fore.RED + "Invalid command. Please enter '/help' for a list of commands.")
            else:
                print(Fore.RED + f"Failed to connect to {esp32_mac_address}.")
    except BleakError as e:
        print(Fore.RED + f"Error while connecting to the ESP32: {e}")
    except Exception as e:
        print(Fore.RED + f"Unknown error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
