from machine import Pin, PWM
from time import sleep_ms
import time
import network
from umqtt.simple import MQTTClient
import _thread  # Para manejar el buzzer en un hilo

# Notas y sus frecuencias correspondientes
B0  = 31
C1  = 33
CS1 = 35
D1  = 37
DS1 = 39
E1  = 41
F1  = 44
FS1 = 46
G1  = 49
GS1 = 52
A1  = 55
AS1 = 58
B1  = 62
C2  = 65
CS2 = 69
D2  = 73
DS2 = 78
E2  = 82
F2  = 87
FS2 = 93
G2  = 98
GS2 = 104
A2  = 110
AS2 = 117
B2  = 123
C3  = 131
CS3 = 139
D3  = 147
DS3 = 156
E3  = 165
F3  = 175
FS3 = 185
G3  = 196
GS3 = 208
A3  = 220
AS3 = 233
B3  = 247
C4  = 262
CS4 = 277
D4  = 294
DS4 = 311
E4  = 330
F4  = 349
FS4 = 370
G4  = 392
GS4 = 415
A4  = 440
AS4 = 466
B4  = 494
C5  = 523
CS5 = 554
D5  = 587  # Aquí está la definición para D5
DS5 = 622
E5  = 659
F5  = 698
FS5 = 740
G5  = 784
GS5 = 831
A5  = 880
AS5 = 932
B5  = 988
C6  = 1047
CS6 = 1109
D6  = 1175
DS6 = 1245
E6  = 1319
F6  = 1397
FS6 = 1480
G6  = 1568
GS6 = 1661
A6  = 1760
AS6 = 1865
B6  = 1976
C7  = 2093
CS7 = 2217
D7  = 2349
DS7 = 2489
E7  = 2637
F7  = 2794
FS7 = 2960
G7  = 3136
GS7 = 3322
A7  = 3520
AS7 = 3729
B7  = 3951
C8  = 4186
CS8 = 4435
D8  = 4699
DS8 = 4978

# Lista de notas para "Noche de Paz"
noche_de_paz = [
    E5, E5, F5, G5, G5, F5, E5, D5, 
    C5, C5, D5, E5, F5, G5, G5, F5, E5,
    E5, E5, F5, G5, G5, F5, E5, D5,
    C5, C5, D5, E5, F5, G5, G5, F5, E5,
    E5, E5, F5, G5, G5, F5, E5, D5, 
    C5, C5, D5, E5, F5, G5, G5, F5, E5
]

# Configuración de LEDs (12 pines)
ledPins = [15, 2, 4, 16, 17, 5, 18, 19, 21, 13, 12, 14]
leds = [Pin(pin, Pin.OUT) for pin in ledPins]

# Clase para manejar el buzzer
class Buzzer:
    def __init__(self, sig_pin):
        self.pwm = PWM(Pin(sig_pin, Pin.OUT))
        self.stop_playing = False  # Variable de control para detener la melodía

    def play(self, melody, wait, duty):
        self.stop_playing = False  # Asegurarse de que pueda empezar a reproducirse
        for i, note in enumerate(melody):
            if self.stop_playing:
                self.pwm.duty(0)  # Apagar buzzer inmediatamente
                break  # Salir del bucle si se recibe la orden de apagar
            # Configurar frecuencia y encender buzzer
            self.pwm.freq(note)
            self.pwm.duty(duty)
            
            # Sincronizar LEDs
            led_index = i % len(leds)  # Elegir LED en base a la nota actual
            leds[led_index].value(1)  # Encender LED
            sleep_ms(wait)
            leds[led_index].value(0)  # Apagar LED
        
        # Apagar buzzer al finalizar
        self.pwm.duty(0)

    def stop(self):
        self.stop_playing = True  # Cambiar la bandera para detener la melodía
        self.pwm.duty(0)  # Detener el buzzer inmediatamente

# Función para conectar al Wi-Fi
def conectar_wifi():
    print("Conectando a Wi-Fi...")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect('UTNG_GUEST', 'R3d1nv1t4d0s#UT')  # Cambia por tu SSID y contraseña
    timeout = 30
    while not sta_if.isconnected() and timeout > 0:
        print("Esperando conexión Wi-Fi...")
        time.sleep(1)
        timeout -= 1
    if sta_if.isconnected():
        print("Conexión Wi-Fi establecida")
        print('Dirección IP:', sta_if.ifconfig()[0])
    else:
        print("No se pudo conectar a Wi-Fi")

# Conexión al broker MQTT
client_id = "esp32_buzzer"
mqtt_server = "broker.emqx.io"  # Nombre de tu broker MQTT
topic_buzzer = "gds0642/buzzer_control"
topic_led = "gds0642/led_control"
client = MQTTClient(client_id, mqtt_server)

# Estado de la reproducción
playing = False

# Función para manejar el mensaje recibido de MQTT
def handle_mqtt_message(topic, msg):
    global playing
    if topic.decode('utf-8') == topic_buzzer:  # Si es el mensaje del buzzer
        if msg == b"1" and not playing:
            # Reproducir la melodía inmediatamente
            print("Reproduciendo Noche de Paz")
            playing = True
            _thread.start_new_thread(buzzer.play, (noche_de_paz, 400, 512))
        elif msg == b"0" and playing:
            # Detener la reproducción inmediatamente
            print("Apagando el buzzer")
            buzzer.stop()  # Detener la melodía y apagar el buzzer
            playing = False

    elif topic.decode('utf-8') == topic_led:  # Si es el mensaje de control de LEDs
        if msg == b"1":  # Encender LEDs
            print("Encendiendo los LEDs...")
            control_leds(1)
        elif msg == b"0":  # Apagar LEDs
            print("Apagando los LEDs...")
            control_leds(0)

def control_leds(state):
    for led in leds:
        led.value(state)

# Función para reconectar en caso de fallo de conexión MQTT
def reconnect():
    while True:
        try:
            print("Conectando al broker...")
            client.connect()
            print("Conexión establecida.")
            client.set_callback(handle_mqtt_message)  # Establecer el callback aquí
            client.subscribe(topic_buzzer)
            client.subscribe(topic_led)  # Suscribirse también al control de LEDs
            print(f"Suscripción al tema '{topic_buzzer}' y '{topic_led}' realizada.")
            break
        except Exception as e:
            print(f"Error de conexión MQTT. Intentando reconectar... {e}")
            time.sleep(5)  # Esperar 5 segundos antes de intentar de nuevo

# Inicializar buzzer
buzzer = Buzzer(14)

# Conectar a Wi-Fi antes de conectar al broker MQTT
conectar_wifi()

# Intentar conectar al broker MQTT y suscribirse
reconnect()

# Loop principal de MQTT
try:
    while True:
        client.wait_msg()  # Esperar mensajes MQTT
except KeyboardInterrupt:
    print("Desconectando del broker MQTT")
    client.disconnect()
