from machine import Pin, PWM, UART
from utils import _parse_hc05_frames, FRAME_LENGTH, MotorController

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

# Move UART away from motor pins to reduce electrical interference
uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17), bits=8, parity=None, stop=1)  # UART0 on pins GP16, GP17

# --- HC-05 binary frame parsing ---
# Frames are 8 bytes: 0xff 0x1 0x1 0x1 0x2 0x0 <dir_code> 0x0
# dir_code: 0x1=Forward, 0x2=Backward, 0x4=Left, 0x8=Right


# Define HC-SR04 pins
# TRIG = Pin(27, Pin.OUT) # pin 31
# ECHO = Pin(28, Pin.IN) # pin 34

# PWM and default speed settings
# Duty range: 0..65535 (use duty_u16). DEFAULT_SPEED is a safe starting value you can change.
DEFAULT_SPEED = 60000  # Increased for faster movement (max: 65535)
# Reduced PWM frequency to minimize EMI interference with UART
PWM_FREQ = 2000

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

# Initialize the independent motor controller
motor = MotorController(IN1_pwm, IN2_pwm, IN3_pwm, IN4_pwm, DEFAULT_SPEED)
pre_cmd = 'F'

# --- Main loop ---
def main():
    uart.read()  # Clear any existing data
    
    state_names = {
        'F': 'Forward', 
        'B': 'Backward', 
        'L': 'Left turn', 
        'R': 'Right turn', 
        'S': 'Stopped'
    }
    
    while True:
        # Check Bluetooth commands (non-blocking)
        if uart.any():
            try:
                # Read all available data
                data = uart.read(FRAME_LENGTH)
                if data:
                    print("Raw bytes received:", data)
                    print("Length of data:", len(data))
                    
                    # Parse frames independently
                    binary_cmds = _parse_hc05_frames(data)
                    
                    if binary_cmds:
                        # Process each command
                        for cmd in binary_cmds:
                            print("Parsed HC-05 frame cmd:", cmd)
                            
                            if cmd == 'E':
                                # Update motor state (motor controller handles execution)
                                if motor.update_state(pre_cmd):
                                    print(f"State changed to: {state_names[pre_cmd]}")
                                pre_cmd = 'E'
                            else:
                                pre_cmd = cmd
                            
            except UnicodeError as e:
                print("Error decoding data:", e)
                print("Raw data:", data)
            except Exception as e:
                print("Error processing data:", e)
        
        # Motor controller maintains its own state,
        # no need to continuously call execute_movement here

if __name__ == '__main__':
    main()