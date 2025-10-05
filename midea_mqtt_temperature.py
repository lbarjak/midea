import json
import logging
import paho.mqtt.client as mqtt
from midea_beautiful import appliance_state

# Kényes adatok betöltése fájlból
with open("midea.json", "r") as f:
    config = json.load(f)

MQTT_BROKER = config["MQTT_BROKER"]
MQTT_TOPIC = config["MQTT_TOPIC"]
APPLIANCE_ADDRESS = config["APPLIANCE_ADDRESS"]
TOKEN = config["TOKEN"]
KEY = config["KEY"]

# Saját logolás csak hőmérsékletre
logging.basicConfig(level=logging.ERROR)  # Csak hibákat ír ki, a saját print marad!

# Külső modul logolásának némítása (ha zavaró)
logging.getLogger("midea_beautiful").setLevel(logging.ERROR)

appliance = appliance_state(
    address=APPLIANCE_ADDRESS,
    token=TOKEN,
    key=KEY,
)

def on_message(client, userdata, msg, properties=None):
    try:
        payload = json.loads(msg.payload.decode())
        temp = payload.get("temperature")

        appliance.refresh()
        prev_set = appliance.state.target_temperature
        out_temp = appliance.state.outdoor_temperature
        in_temp = appliance.state.indoor_temperature
        print(f"polcon: {temp}, set: {prev_set}, kint: {out_temp}, bent felül: {in_temp}")

        target_temp = None

        if temp >= 23.5:
            target_temp = 21.5
        # 23.5 - 23.3 között a 0.2 fok a hiszterézis növeléséhez van
        elif temp < 23.3:
            target_temp = 24
        # Ezzel a beállítással 23.24 - 23.67 adódott, azaz 0.43 fok a hiszterézis

        if target_temp and prev_set != target_temp:
            appliance.set_state(target_temperature=target_temp)
            print(f"Hőmérséklet beállítva: {target_temp}°C (indoor temperature: {temp})")

    except Exception:
        pass  # Hibát némán elnyeljük, nem írunk semmit

client = mqtt.Client(protocol=mqtt.MQTTv5, callback_api_version=2)
client.on_message = on_message
client.connect(MQTT_BROKER)
client.subscribe(MQTT_TOPIC, qos=2)
client.loop_forever()
