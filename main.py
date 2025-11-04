import time
import random
from machine import Pin, PWM, UART

prev_dist = 100  # Initialize previous distance
# Define motor pins
ENA = PWM(Pin(2))
IN1 = Pin(3, Pin.OUT)# Motor A pin 5
IN2 = Pin(4, Pin.OUT)# Motor A pin 6
IN3 = Pin(5, Pin.OUT)# Motor B pin 7
IN4 = Pin(6, Pin.OUT)# Motor B pin 9
ENB = PWM(Pin(7))

uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1), bits=8, parity=None, stop=1)  # UART0 on pins GP0, GP1

# Define HC-SR04 pins
TRIG = Pin(27, Pin.OUT) # pin 31
ECHO = Pin(28, Pin.IN) # pin 34

# Set motor speed (0–65025)
speed = 1000
ENA.freq(500)
ENB.freq(500)
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

def turn_left():
    IN1.on()
    IN2.off()
    IN3.off()
    IN4.on()

def turn_right():
    IN1.off()
    IN2.on()
    IN3.on()
    IN4.off()

def left():
    turn_left()
    time.sleep(0.2)  # Turn for half a second
    forward()

def right():
    turn_right()
    time.sleep(0.2)  # Turn for half a second
    forward()

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
    uart.read()  # Clear any existing data
    current_movement = None  # Track current movement state
    
    while True:
        # Check Bluetooth commands
        if uart.any():
            try:
                # Read all available data
                data = uart.read()
                if data:
                    # Show exact raw bytes so we can see control characters
                    print("Raw bytes received:", [hex(b) for b in data])
                    print("Length of data:", len(data))
                    try:
                        # decode but ignore undecodable bytes so we can still inspect
                        text = data.decode('ascii', 'ignore')
                        print("As text:", repr(text))
                        print("ASCII values:", [ord(c) for c in text])

                        # Sanitize: remove common control characters first (CR/LF)
                        text = text.replace('\r', '').replace('\n', '')
                        # Keep only printable ASCII characters (32..126) — works on MicroPython
                        text_sanitized = ''.join(c for c in text if 32 <= ord(c) <= 126)
                        print("Sanitized text:", repr(text_sanitized))

                        if not text_sanitized:
                            print("No printable characters after sanitizing")
                        else:
                            # Update movement based on new command
                            cmd = text_sanitized
                            if cmd == 'F':
                                current_movement = forward
                                print("Set continuous Forward movement")
                            elif cmd == 'B':
                                current_movement = backward
                                print("Set continuous Backward movement")
                            elif cmd == 'L':
                                left()  # This will turn left and set to forward
                                current_movement = forward
                                print("Turned Left and moving Forward")
                            elif cmd == 'R':
                                right()  # This will turn right and set to forward
                                current_movement = forward
                                print("Turned Right and moving Forward")
                            elif cmd == 'S':
                                current_movement = stop
                                print("Stopped")
                            else:
                                print("Unknown command:", repr(cmd))
                    except UnicodeError:
                        print("Could not decode as ASCII")
            except UnicodeError as e:
                print("Error decoding data:", e)
                print("Raw data:", data)
            except Exception as e:
                print("Error processing data:", e)

        
        # Execute current movement if set
        if current_movement:
            current_movement()
            
            # If not stopped or moving backward, switch to forward movement
            if current_movement not in [stop, backward]:
                current_movement = forward
            
            # If moving forward, check for obstacles
            if current_movement == forward:
                dist = get_distance()
                if dist < 20 and prev_dist < 20:
                    print("Obstacle detected at", dist, "cm - Stopping!")
                    stop()
                    current_movement = stop
                prev_dist = dist  # Update previous distance
        
        time.sleep(0.05)

except KeyboardInterrupt:
    stop()
    print("Program stopped")