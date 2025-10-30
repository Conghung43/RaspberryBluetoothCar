import time
import random
from machine import Pin, PWM

# Define motor pins
ENA = PWM(Pin(2))
IN1 = Pin(3, Pin.OUT)# Motor A pin 5
IN2 = Pin(4, Pin.OUT)# Motor A pin 6
IN3 = Pin(5, Pin.OUT)# Motor B pin 7
IN4 = Pin(6, Pin.OUT)# Motor B pin 9
ENB = PWM(Pin(7))

# Define HC-SR04 pins
TRIG = Pin(27, Pin.OUT) # pin 31
ECHO = Pin(28, Pin.IN) # pin 34

# Set motor speed (0–65025)
speed = 30000
ENA.freq(1000)
ENB.freq(1000)
ENA.duty_u16(speed)
ENB.duty_u16(speed)

# --- Motor control functions ---
def forward():
    IN1.on()
    IN2.off()
    IN3.on()
    IN4.off()

def backward():
    IN1.off()
    IN2.on()
    IN3.off()
    IN4.on()

def left():
    IN1.on()
    IN2.off()
    IN3.off()
    IN4.on()

def right():
    IN1.off()
    IN2.on()
    IN3.on()
    IN4.off()

def stop():
    IN1.off()
    IN2.off()
    IN3.off()
    IN4.off()

# --- Distance measurement function ---
def get_distance():
    TRIG.low()
    time.sleep_us(2)
    TRIG.high()
    time.sleep_us(10)
    TRIG.low()

    # Wait for echo start
    while ECHO.value() == 0:
        signaloff = time.ticks_us()
    # Wait for echo end
    while ECHO.value() == 1:
        signalon = time.ticks_us()

    timepassed = time.ticks_diff(signalon, signaloff)
    distance = (timepassed * 0.0343) / 2  # cm
    return distance

# --- Main loop ---
try:
    while True:
        dist = get_distance()
        print("Distance:", dist, "cm")

        if dist < 40:  # If object detected within 10 cm
            stop()
            time.sleep(0.2)
            turn_dir = random.choice(["left", "right"])  # type: ignore
            print("Obstacle detected! Turning", turn_dir)

            if turn_dir == "left":
                left()
            else:
                right()

            time.sleep(0.4)  # Turn time
            stop()
            time.sleep(0.2)

        else:
            forward()

        time.sleep(0.05)

except KeyboardInterrupt:
    stop()
    print("Program stopped")