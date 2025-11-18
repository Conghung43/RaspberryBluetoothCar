# Raspberry Pi Pico 2W Bluetooth Robot Car

A MicroPython-based robot car project for Raspberry Pi Pico 2W with Bluetooth control (HC-05/HC-06), dual DC motors, and optional ultrasonic sensor support.

## Features

- **Bluetooth Control**: Wireless control via HC-05/HC-06 Bluetooth module
- **Dual Motor Control**: L9110 or similar H-bridge motor driver support with PWM speed control
- **Real-time Commands**: Forward, Backward, Left, Right, and Stop movements
- **Utility Scripts**: 
  - Baudrate detection for Bluetooth module
  - Bluetooth module reset and AT command interface
- **Optional Obstacle Detection**: HC-SR04 ultrasonic sensor support (commented out by default)

## Hardware Requirements

### Main Components
- **Raspberry Pi Pico 2W** (or Pico W)
- **HC-05 or HC-06 Bluetooth Module**
- **L9110 Dual Motor Driver** (or compatible H-bridge driver)
- **2x DC Motors**
- **Power Supply** (suitable for motors and Pico)
- **Robot Chassis** (with wheels)

### Optional Components
- **HC-SR04 Ultrasonic Sensor** (for obstacle detection)

### Pin Connections

#### Motor Driver (L9110)
| Pico Pin | Function | Connection |
|----------|----------|------------|
| GP2 | ENA (PWM) | Motor Driver Enable A |
| GP3 | IN1 (PWM) | Motor A Input 1 |
| GP4 | IN2 (PWM) | Motor A Input 2 |
| GP5 | IN3 (PWM) | Motor B Input 1 |
| GP6 | IN4 (PWM) | Motor B Input 2 |
| GP7 | ENB (PWM) | Motor Driver Enable B |

#### Bluetooth Module (HC-05/HC-06)
| Pico Pin | Function | Connection |
|----------|----------|------------|
| GP0 | UART0 TX | BT Module RX |
| GP1 | UART0 RX | BT Module TX |
| 3.3V | VCC | BT Module VCC |
| GND | GND | BT Module GND |

#### Ultrasonic Sensor (Optional - HC-SR04)
| Pico Pin | Function | Connection |
|----------|----------|------------|
| GP27 | TRIG | Ultrasonic TRIG |
| GP28 | ECHO | Ultrasonic ECHO |

#### Bluetooth Reset Control (Optional)
| Pico Pin | Function | Connection |
|----------|----------|------------|
| GP22 | RESET | BT Module RST |
| GP21 | KEY | BT Module KEY/EN |

## Software Requirements

- **Visual Studio Code** (VS Code)
- **MicroPico Extension** for VS Code
- **MicroPython** (latest version recommended)
- **Bluetooth Serial Terminal** app on your mobile device (e.g., Serial Bluetooth Terminal for Android)

## Installation

### 1. Install VS Code and MicroPico Extension

1. Download and install [Visual Studio Code](https://code.visualstudio.com/)
2. Open VS Code and go to Extensions (Ctrl+Shift+X or Cmd+Shift+X on Mac)
3. Search for "MicroPico" and install the extension by paulober
4. Restart VS Code if prompted

### 2. Install MicroPython on Pico 2W

1. Download the latest MicroPython firmware for Pico W from [micropython.org](https://micropython.org/download/rp2-pico-w/)
2. Hold the BOOTSEL button on the Pico while connecting it to your computer via USB
3. The Pico will appear as a USB mass storage device (RPI-RP2)
4. Copy the `.uf2` firmware file to the RPI-RP2 drive
5. The Pico will reboot automatically with MicroPython installed

### 3. Configure MicroPico in VS Code

1. Open your project folder in VS Code (File → Open Folder)
2. Connect your Pico to the computer via USB
3. Open the Command Palette (Ctrl+Shift+P or Cmd+Shift+P on Mac)
4. Type "MicroPico: Configure Project" and select it
5. Follow the prompts to select your Pico device
6. The extension will create a `.micropico` folder with configuration

### 4. Upload Project Files to Pico

1. In VS Code, ensure your Pico is connected and recognized by MicroPico
2. Right-click on `main.py` in the Explorer and select "Upload current file to Pico"
3. Repeat for other files:
   - `bt_reset.py` - Bluetooth module reset utility (optional)
   - `detect_baudrate.py` - Baudrate detection utility (optional)
4. Alternatively, you can upload the entire project:
   - Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
   - Select "MicroPico: Upload project to Pico"

### 5. Configure Bluetooth Module (if needed)

If your HC-05/HC-06 module needs configuration:

1. Open the MicroPico terminal in VS Code (View → Terminal or use MicroPico status bar)
2. Connect to your Pico's REPL
3. Run the following commands:

```python
import bt_reset

# Test AT communication
bt_reset.send_at('AT')

# Get module name
bt_reset.send_at('AT+NAME?')

# Set baud rate (if needed)
bt_reset.send_at('AT+UART=9600,0,0')
```

## Usage

### Running the Robot

1. **Power on the robot**
2. **Pair your Bluetooth device**:
   - Search for Bluetooth devices on your phone/computer
   - Default name is usually "HC-05" or "HC-06"
   - Default PIN is typically "1234" or "0000"
3. **Connect via Bluetooth Serial Terminal**
4. **Send control commands**:
   - `F` - Move Forward
   - `B` - Move Backward
   - `L` - Turn Left (brief turn then forward)
   - `R` - Turn Right (brief turn then forward)
   - `S` - Stop

### Auto-start on Boot

To make `main.py` run automatically when the Pico powers on:

1. The file is already named `main.py` - MicroPython automatically executes this file on boot
2. Ensure `main.py` is uploaded to the root directory of the Pico
3. You can verify by opening the MicroPico file explorer in VS Code

### Baudrate Detection

If you're unsure about your Bluetooth module's baud rate:

```python
# Upload and run detect_baudrate.py
# The script will test common baud rates (9600, 38400, 57600, 115200)
# Send data from your Bluetooth terminal during the test
```

### Debugging

Monitor the serial output using MicroPico's integrated terminal in VS Code:

1. Open the Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
2. Select "MicroPico: Connect"
3. The terminal will show:
   - Raw bytes received from Bluetooth
   - Decoded commands
   - Motor states
   - Error messages

You can also use the MicroPico REPL to:
- Test individual functions interactively
- Check variable values in real-time
- Run diagnostic commands

## Configuration

### Motor Speed Adjustment

In `main.py`, adjust these constants:

```python
DEFAULT_SPEED = 40000  # Range: 0-65535
PWM_FREQ = 1500        # PWM frequency in Hz
```

### UART Settings

Default UART configuration:

```python
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1), bits=8, parity=None, stop=1)
```

Change `baudrate` if your Bluetooth module uses a different rate.

### Enable Obstacle Detection

Uncomment the HC-SR04 related code in `main.py`:

1. Uncomment pin definitions (lines ~17-18)
2. Uncomment `get_distance()` function (lines ~105-122)
3. Uncomment obstacle detection logic in main loop (lines ~195-200)

## Troubleshooting

### Bluetooth Not Connecting
- Check pin connections (TX/RX are crossed between devices)
- Verify baud rate matches module configuration
- Ensure module is powered (LED should blink when unpaired)
- Run `detect_baudrate.py` to find correct baud rate

### Motors Not Working
- Check motor driver connections and power supply
- Verify PWM pins are correctly configured
- Test individual motor functions in MicroPico REPL (use Command Palette → "MicroPico: Connect")
- Check motor driver enable pins
- Verify sufficient power supply for motors (separate from Pico power if needed)

### No Response to Commands
- Monitor REPL for incoming data
- Check for correct command format (single characters)
- Clear any buffered data: `uart.read()`
- Verify Bluetooth terminal sends ASCII characters

### Commands Appear Garbled
- Raw byte output helps debug encoding issues
- Check for extra line endings or control characters
- Adjust text sanitization in code if needed

## Project Structure

```
PICO2W/
├── main.py              # Main robot control program
├── bt_reset.py          # Bluetooth module reset utility
├── detect_baudrate.py   # Baudrate detection utility
└── README.md            # This file
```

## Code Overview

### main.py
- Motor control functions (forward, backward, left, right, stop)
- PWM-based speed control
- Bluetooth UART communication
- Command parsing and sanitization
- Continuous movement state management

### bt_reset.py
- Hardware reset functionality for Bluetooth module
- AT mode entry for module configuration
- AT command interface for module programming
- Configurable for different pin setups

### detect_baudrate.py
- Automatic baud rate detection
- Tests common baud rates (9600, 38400, 57600, 115200)
- Displays raw and decoded data for debugging

## License

This project is open source and available for educational and personal use.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## Credits

Built for Raspberry Pi Pico 2W using MicroPython.
