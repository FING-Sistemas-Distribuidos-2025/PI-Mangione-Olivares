import queue
import threading
import time
import paho.mqtt.client as mqtt

broker_ip = "192.168.58.255"  # IP del broker (la misma usada por el productor)
topic = "cola/mensajes"
client_id = "consumidor_mensajes"

buffer = queue.Queue()

def on_connect(client, userdata, flags, rc):
    print("Conectado con código", rc)
    client.subscribe(topic)

def on_message(client, userdata, msg):
    mensaje = msg.payload.decode()
    print(f"[Recibido] -> Encolando: {mensaje}")
    buffer.put(mensaje)

def consumir():
    while True:
        if not buffer.empty():
            mensaje = buffer.get()
            print(f"[Consumido] -> {mensaje}")
        time.sleep(1)

client = mqtt.Client(client_id)
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_ip, 1883, 60)

threading.Thread(target=consumir, daemon=True).start()
client.loop_forever()
