from machine import Pin, PWM, time_pulse_us
from utime import sleep, ticks_ms, ticks_diff

# Configuración de pines y módulos
trigger_pin = Pin(18, Pin.OUT)  # Pin de disparo (trigger)
echo_pin = Pin(5, Pin.IN)      # Pin de eco (echo)
servo_15 = PWM(Pin(15), freq=50)  # Servo en el pin 15 (brazo 1)
servo_16 = PWM(Pin(16), freq=50)  # Servo en el pin 16 (brazo 2)
servo_19 = PWM(Pin(19), freq=50)  # Servo en el pin 19 (tercer servo)

# Clase Buzzer
class Buzzer:
    def __init__(self, sig_pin):
        self.pwm = PWM(Pin(sig_pin, Pin.OUT))  # Iniciar el buzzer en el pin 4
    
    def play(self, melody, wait, duty):
        for note in melody:
            self.pwm.freq(note)  # Establecer la frecuencia de la nota
            self.pwm.duty(duty)  # Encender el buzzer con el duty deseado
            sleep(wait)  # Esperar la duración de la nota
            self.pwm.duty(0)  # Apagar el buzzer entre notas
            sleep(0.05)  # Pausa pequeña entre notas para evitar que se mezclen

# Instanciar el buzzer en el pin 4
buzzer = Buzzer(4)  # Conectamos el buzzer al pin 4

# Definir la melodía "Jingle Bells"
jingle_bells = [
    659, 659, 659, 659, 659, 659, 659, 659, 659, 659, 659, 784, 784, 784, 659, 659, 659, 659,
    659, 659, 659, 784, 784, 784, 659, 659, 659, 659, 659, 659, 659, 659, 659, 784, 784, 659, 
    659, 659, 659, 659, 659, 659, 659, 659, 659, 659, 784, 784, 784, 659
]

# Función para mover servos de forma lenta (gradualmente)
def move_servo_slow(servo, start_value, end_value, steps=20, delay=0.05):
    """ Mueve un servo desde start_value a end_value en pasos pequeños """
    step_size = (end_value - start_value) / steps
    for step in range(steps):
        current_value = start_value + step * step_size
        move_servo(servo, current_value)
        sleep(delay)

# Función para mover servos a un rango de 8000 a 1800 (correspondiente a 0 a 180 grados)
def move_servo(servo, value):
    min_value = 1800  # Corresponde a 0 grados
    max_value = 8000  # Corresponde a 180 grados
    duty_value = int(min_value + (value / 180) * (max_value - min_value))
    servo.duty_u16(duty_value)

# Función para resetear los servos a su posición original (90 grados)
def reset_servos():
    move_servo_slow(servo_15, 90, 90)  # Resetear servo 15 a 90 grados
    move_servo_slow(servo_16, 90, 90)  # Resetear servo 16 a 90 grados
    move_servo_slow(servo_19, 90, 90)  # Resetear servo 19 a 90 grados
    sleep(1)  # Pausa para asegurar que los servos lleguen a su posición

# Función para medir la distancia con el sensor ultrasónico
def measure_distance():
    trigger_pin.value(0)  # Coloca el pin de trigger en bajo
    sleep(0.000002)  # Espera antes de generar el pulso
    trigger_pin.value(1)  # Coloca el pin de trigger en alto
    sleep(0.00001)   # Pulso de 10 microsegundos
    trigger_pin.value(0)  # Coloca el pin de trigger en bajo
    
    pulse_time = time_pulse_us(echo_pin, 1)  # Medir el tiempo de eco
    distance = pulse_time * 0.0343 / 2  # Convertir a distancia en cm
    return distance

# Ciclo principal
reset_servos()  # Llamamos a la función de reset al inicio para que todos los servos inicien en 90 grados

while True:
    try:
        distancia = measure_distance()  # Medimos la distancia en cm
        print("Distancia medida: {:.2f} cm".format(distancia))

        # Si la distancia es menor a 30 cm, mover los servos hacia el lado contrario
        if distancia < 30:
            move_servo_slow(servo_15, 90, 20)  # Mover el primer brazo (servo 15) a 135 grados
            move_servo_slow(servo_19, 90, 20)  # Mover el tercer servo a 135 grados
            # No mover el segundo brazo

        # Si la distancia está entre 30 cm y 100 cm, mover ambos brazos y reproducir música
        elif 30 <= distancia < 100:
            move_servo_slow(servo_15, 90, 30)  # Mover el primer brazo (servo 15) a 45 grados
            move_servo_slow(servo_16, 90, 30)  # Mover el segundo brazo (servo 16) a 45 grados
            move_servo_slow(servo_19, 90, 30)  # Mover el tercer servo a 45 grados
            buzzer.play(jingle_bells, 0.2, 512)  # Reproducir la melodía "Jingle Bells"

        # Si la distancia está entre 100 cm y 150 cm, mover los dos primeros brazos
        elif 100 <= distancia < 150:
            move_servo_slow(servo_15, 90, 180)  # Mover el primer brazo (servo 15) a 180 grados
            move_servo_slow(servo_16, 90, 180)  # Mover el segundo brazo (servo 16) a 180 grados
            move_servo_slow(servo_19, 90, 180)  # Mover el tercer servo a 180 grados

        # Si la distancia es mayor a 150 cm, resetear los servos
        else:
            reset_servos()  # Resetear todos los servos

    except RuntimeError:
        print("Error de lectura del sensor")
    
    sleep(1)  # Esperar un segundo antes de la siguiente lectura


