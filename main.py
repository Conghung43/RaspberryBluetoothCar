import time
import random
from machine import Pin, PWM, UART

prev_dist = 100  # Initialize previous distance
# Define motor pins (use PWM on direction pins so we can control speed per direction)
# Note: for L9110 style drivers we PWM the active direction pin and keep the opposite pin 0.
ENA = PWM(Pin(2))  # kept for compatibility if your board has an enable pin (unused by L9110)
# Use PWM objects for IN1..IN4 so we can apply duty_u16 for speed control
IN1_pwm = PWM(Pin(3))  # Motor A input 1 (was IN1)
IN2_pwm = PWM(Pin(4))  # Motor A input 2 (was IN2)
IN3_pwm = PWM(Pin(5))  # Motor B input 1 (was IN3)
IN4_pwm = PWM(Pin(6))  # Motor B input 2 (was IN4)
ENB = PWM(Pin(7))

uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1), bits=8, parity=None, stop=1)  # UART0 on pins GP0, GP1

# Define HC-SR04 pins
# TRIG = Pin(27, Pin.OUT) # pin 31
# ECHO = Pin(28, Pin.IN) # pin 34

# PWM and default speed settings
# Duty range: 0..65535 (use duty_u16). DEFAULT_SPEED is a safe starting value you can change.
DEFAULT_SPEED = 40000
PWM_FREQ = 1500

# Configure PWM frequency for all PWM pins
ENA.freq(PWM_FREQ)
ENB.freq(PWM_FREQ)
IN1_pwm.freq(PWM_FREQ)
IN2_pwm.freq(PWM_FREQ)
IN3_pwm.freq(PWM_FREQ)
IN4_pwm.freq(PWM_FREQ)

# Initialize all direction PWMs to 0 (stopped)
IN1_pwm.duty_u16(0)
IN2_pwm.duty_u16(0)
IN3_pwm.duty_u16(0)
IN4_pwm.duty_u16(0)

# --- Motor control functions ---
def set_duty(pwm_obj, u16):
    """Set duty safely (0..65535)."""
    pwm_obj.duty_u16(max(0, min(65535, int(u16))))

# Motor A helpers (IN1_pwm / IN2_pwm)
def motorA_forward(u16=DEFAULT_SPEED+PWM_FREQ):
    set_duty(IN2_pwm, 0)
    set_duty(IN1_pwm, u16)

def motorA_backward(u16=DEFAULT_SPEED+PWM_FREQ):
    set_duty(IN1_pwm, 0)
    set_duty(IN2_pwm, u16)

def motorA_stop():
    set_duty(IN1_pwm, 0)
    set_duty(IN2_pwm, 0)

# Motor B helpers (IN3_pwm / IN4_pwm)
def motorB_forward(u16=DEFAULT_SPEED):
    set_duty(IN4_pwm, 0)
    set_duty(IN3_pwm, u16)

def motorB_backward(u16=DEFAULT_SPEED):
    set_duty(IN3_pwm, 0)
    set_duty(IN4_pwm, u16)

def motorB_stop():
    set_duty(IN3_pwm, 0)
    set_duty(IN4_pwm, 0)

def forward():
    motorA_forward()
    motorB_forward()

def backward():
    motorA_backward()
    motorB_backward()

def turn_left():
    # Spin in place: A forward, B backward
    motorA_forward()
    motorB_backward()

def turn_right():
    # Spin in place: A backward, B forward
    motorA_backward()
    motorB_forward()

def left():
    turn_left()
    time.sleep(0.2)  # Turn for a short duration
    forward()

def right():
    turn_right()
    time.sleep(0.2)  # Turn for a short duration
    forward()

def stop():
    motorA_stop()
    motorB_stop()

# --- Distance measurement function ---
# def get_distance():
#     TRIG.low()
#     time.sleep_us(2)
#     TRIG.high()
#     time.sleep_us(10)
#     TRIG.low()

#     # Wait for echo start
#     while ECHO.value() == 0:
#         signaloff = time.ticks_us()
#     # Wait for echo end
#     while ECHO.value() == 1:
#         signalon = time.ticks_us()

#     timepassed = time.ticks_diff(signalon, signaloff)
#     distance = (timepassed * 0.0343) / 2  # cm
#     return distance

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
            # if current_movement == forward:
            #     dist = get_distance()
            #     if dist < 20 and prev_dist < 20:
            #         print("Obstacle detected at", dist, "cm - Stopping!")
            #         stop()
            #         current_movement = stop
            #     prev_dist = dist  # Update previous distance
        
        time.sleep(0.05)

except KeyboardInterrupt:
    stop()
    print("Program stopped")