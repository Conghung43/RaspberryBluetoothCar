import time

_HEADER_PATTERN = b"\xff\x01\x01\x01\x02\x00"  # first 6 bytes
_DIR_INDEX = 6
_TAIL_EXPECTED = 0x00
_direction_map = {0:'E',1: 'F', 2: 'B', 4: 'L', 8: 'R', 16: 'S'}  # Added 16 (0x10) for Stop
FRAME_LENGTH = 8

def _is_valid_frame(frame):
    """Validate frame integrity to filter corrupted data from motor EMI."""
    if len(frame) != FRAME_LENGTH:
        return False
    # Check exact header pattern
    if not frame.startswith(_HEADER_PATTERN):
        return False
    # Check tail byte
    if frame[7] != _TAIL_EXPECTED:
        return False
    # Check direction code is valid
    if frame[_DIR_INDEX] not in _direction_map:
        return False
    return True

def _parse_hc05_frames(buf):
    cmds = []
    i = 0
    n = len(buf)
    while i < n:
        # Look for header start
        if buf[i] == 0xff:
            remaining = n - i
            if remaining < FRAME_LENGTH:
                # Incomplete frame, wait for more bytes
                break
            candidate = buf[i:i+FRAME_LENGTH]
            # Use stricter validation to reject corrupted frames
            if _is_valid_frame(candidate):
                dir_code = candidate[_DIR_INDEX]
                cmds.append(_direction_map[dir_code])
                # Consume valid frame
                i += FRAME_LENGTH
                continue
            else:
                # Invalid frame at this 0xff; skip this byte and continue searching
                i += 1
                continue
        else:
            i += 1
    return cmds


# --- Motor Control Module (Independent) ---
# This module handles all motor control operations independently
# from the main program data parsing

class MotorController:
    """Independent motor controller that manages movement state."""
    
    def __init__(self, in1_pwm, in2_pwm, in3_pwm, in4_pwm, default_speed=40000):
        self.IN1_pwm = in1_pwm
        self.IN2_pwm = in2_pwm
        self.IN3_pwm = in3_pwm
        self.IN4_pwm = in4_pwm
        self.default_speed = default_speed
        self.current_state = 'S'  # Start stopped
        
    def set_duty(self, pwm_obj, u16):
        """Set duty safely (0..65535)."""
        pwm_obj.duty_u16(max(0, min(65535, int(u16))))
    
    # Motor A helpers (IN1_pwm / IN2_pwm)
    def motorA_forward(self, u16=None):
        if u16 is None:
            u16 = self.default_speed
        self.set_duty(self.IN2_pwm, 0)
        self.set_duty(self.IN1_pwm, u16)
    
    def motorA_backward(self, u16=None):
        if u16 is None:
            u16 = self.default_speed
        self.set_duty(self.IN1_pwm, 0)
        self.set_duty(self.IN2_pwm, u16)
    
    def motorA_stop(self):
        self.set_duty(self.IN1_pwm, 0)
        self.set_duty(self.IN2_pwm, 0)
    
    # Motor B helpers (IN3_pwm / IN4_pwm)
    def motorB_forward(self, u16=None):
        if u16 is None:
            u16 = self.default_speed
        self.set_duty(self.IN4_pwm, 0)
        self.set_duty(self.IN3_pwm, u16)
    
    def motorB_backward(self, u16=None):
        if u16 is None:
            u16 = self.default_speed
        self.set_duty(self.IN3_pwm, 0)
        self.set_duty(self.IN4_pwm, u16)
    
    def motorB_stop(self):
        self.set_duty(self.IN3_pwm, 0)
        self.set_duty(self.IN4_pwm, 0)
    
    def forward(self):
        # Start with a high-speed burst to avoid stalling
        self.motorA_forward(65535)  # Max speed
        self.motorB_forward(65535)  # Max speed
        time.sleep(0.2)  # Short burst duration
        self.motorA_forward()
        self.motorB_forward()

    def backward(self):
        # Start with a high-speed burst to avoid stalling
        self.motorA_backward(65535)  # Max speed
        self.motorB_backward(65535)  # Max speed
        time.sleep(0.2)  # Short burst duration
        self.motorA_backward()
        self.motorB_backward()

    def turn_left(self):
        # Start with a high-speed burst to avoid stalling
        self.motorA_forward(65535)  # Max speed
        self.motorB_stop()  # Max speed
        time.sleep(0.2)  # Short burst duration
        self.motorA_forward()
        self.motorB_stop()

    def turn_right(self):
        # Start with a high-speed burst to avoid stalling
        self.motorA_stop()  # Max speed
        self.motorB_forward(65535)  # Max speed
        time.sleep(0.2)  # Short burst duration
        self.motorA_stop()
        self.motorB_forward()
    
    def stop(self):
        self.motorA_stop()
        self.motorB_stop()
    
    def execute_movement(self, state=None):
        """Execute movement based on state. If state is None, use current_state."""
        if state is not None:
            self.current_state = state
        
        if self.current_state == 'F':
            self.forward()
        elif self.current_state == 'B':
            self.backward()
        elif self.current_state == 'L':
            self.turn_left()
        elif self.current_state == 'R':
            self.turn_right()
        elif self.current_state == 'S':
            self.stop()
        elif self.current_state == 'E':
            self.stop()
    
    def update_state(self, new_state):
        """Update state and execute the new movement."""
        if new_state in ['E','F', 'B', 'L', 'R', 'S']:
            self.execute_movement(new_state)
            return True
        return False
    
    def get_state(self):
        """Get current movement state."""
        return self.current_state