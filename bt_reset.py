"""
bt_reset.py

MicroPython helper to reset a Bluetooth module (HC-05/HC-06 style) from a Raspberry Pi Pico.

Features:
- Hardware reset by toggling a GPIO connected to module RST or VCC-enable pin.
- Enter AT mode by driving KEY (or EN) high during power-up (if your module supports it).
- Send simple AT commands over UART and show responses.

Usage:
- Edit the configuration at the top to match the pins you wired:
    RESET_PIN = 22        # pin connected to module RST or VCC-enable (change as needed)
    KEY_PIN = 21          # pin connected to module KEY/EN/STATE for AT-mode selection (optional)
    USE_RESET_PIN = True  # set False if you don't have a reset pin
    USE_KEY_PIN = True    # set False if your module has no KEY pin

- Upload this file to the Pico and run from REPL or import and call functions.

Examples:
    import bt_reset
    bt_reset.hw_reset()
    resp = bt_reset.send_at('AT')

Warning: This script toggles power/reset lines. Make sure wiring is correct and the module's power/logic expectations are met.
"""

from machine import Pin, UART
import time

# ---------- CONFIGURATION (edit for your wiring) ----------
UART_ID = 0
UART_BAUD = 9600
UART_TX_PIN = 0  # GP0
UART_RX_PIN = 1  # GP1

# GPIO pins on the Pico used to control the BT module - change as required
RESET_PIN = 22    # Connect to module RST or to a MOSFET/transistor gate that cuts VCC
KEY_PIN = 21      # Connect to module KEY/EN if available (pull high before power on to enter AT)

USE_RESET_PIN = True
USE_KEY_PIN = False  # set True if you wired KEY or EN pin

# timings (ms)
RESET_PULSE_MS = 200
POST_RESET_WAIT_MS = 500
AT_MODE_POWER_CYCLE_MS = 300
READ_TIMEOUT_MS = 1000

# -----------------------------------------------------------

# Local helper to create UART (does not close existing hardware UARTs)
def _open_uart(baud=UART_BAUD):
    return UART(UART_ID, baudrate=baud, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN), bits=8, parity=None, stop=1)

# Hardware reset: pull reset pin active for pulse_ms then release
def hw_reset(reset_pin=RESET_PIN, pulse_ms=RESET_PULSE_MS, active_low=True):
    """Perform a hardware reset using the given GPIO.

    active_low: if True, drive pin low to reset (typical RST behavior). If False, drive high to reset.
    """
    if not USE_RESET_PIN:
        print("RESET pin usage disabled (USE_RESET_PIN=False). Skipping hw_reset.")
        return

    p = Pin(reset_pin, Pin.OUT)

    if active_low:
        # Ensure released state (high) then pulse low
        p.on()
        time.sleep_ms(50)
        print("Asserting reset (pull low) for {} ms".format(pulse_ms))
        p.off()
        time.sleep_ms(pulse_ms)
        p.on()
    else:
        # Ensure released (low) then pulse high
        p.off()
        time.sleep_ms(50)
        print("Asserting reset (pull high) for {} ms".format(pulse_ms))
        p.on()
        time.sleep_ms(pulse_ms)
        p.off()

    time.sleep_ms(POST_RESET_WAIT_MS)
    print("Hardware reset complete")


def enter_at_mode(key_pin=KEY_PIN, reset_pin=RESET_PIN, key_active_high=True):
    """Try to enter AT mode by asserting KEY pin (or EN) during power-up/reset.

    Steps (typical for HC-05):
      - Drive KEY high
      - Power-cycle / reset module
      - Module should boot into AT mode

    Returns True if sequence executed; does not verify AT-mode automatically.
    """
    if not USE_KEY_PIN:
        print("KEY pin usage disabled (USE_KEY_PIN=False). Skipping enter_at_mode.")
        return False

    k = Pin(key_pin, Pin.OUT)
    print("Setting KEY pin {}".format('HIGH' if key_active_high else 'LOW'))
    if key_active_high:
        k.on()
    else:
        k.off()

    # Small delay to ensure key is seen before power-cycle
    time.sleep_ms(50)

    # Power cycle / reset while KEY is asserted
    if USE_RESET_PIN:
        hw_reset(reset_pin=reset_pin, pulse_ms=AT_MODE_POWER_CYCLE_MS, active_low=True)
    else:
        # If there is no dedicated reset pin, user must power-cycle module manually.
        print("No RESET pin configured; please power-cycle the BT module now while KEY is asserted.")

    # Leave KEY asserted for a short time to allow module to boot in AT mode
    time.sleep_ms(300)
    print("AT mode entry sequence complete (KEY left asserted).")
    return True


def send_at(command, baud=UART_BAUD, timeout_ms=READ_TIMEOUT_MS):
    """Send an AT command over UART and return the response as bytes/string.

    Returns tuple (raw_bytes, decoded_str) where decoded_str may be None if decode fails.
    """
    u = _open_uart(baud)
    cmd = command
    if not cmd.endswith('\r') and not cmd.endswith('\n'):
        cmd = cmd + '\r\n'

    try:
        print("Sending AT command:", repr(command))
        u.write(cmd)

        # wait for response
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        resp = b''
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            if u.any():
                chunk = u.read()
                if chunk:
                    resp += chunk
                    # short delay to allow more data
                    time.sleep_ms(50)
            else:
                time.sleep_ms(10)

        if not resp:
            print("No response received (timeout)")
            return (b'', None)

        print("Raw response:", [hex(b) for b in resp])
        try:
            text = resp.decode('ascii', 'ignore')
            print("Decoded:", repr(text))
            return (resp, text)
        except Exception as e:
            print("Decode failed:", e)
            return (resp, None)
    finally:
        # Close UART by re-initializing to default (optional) -- on Pico, creating a new UART replaces the old
        pass


# Convenience script-run example
if __name__ == '__main__':
    print("bt_reset helper running. Configuration:\n  RESET_PIN={}, USE_RESET_PIN={}\n  KEY_PIN={}, USE_KEY_PIN={}".format(RESET_PIN, USE_RESET_PIN, KEY_PIN, USE_KEY_PIN))
    print("1) Trying to send simple AT to see if module responds at current baud")
    send_at('AT')

    if USE_RESET_PIN:
        print('\n2) Performing hardware reset...')
        hw_reset()
        print('Waiting a bit and probing with AT...')
        time.sleep_ms(500)
        send_at('AT')

    if USE_KEY_PIN:
        print('\n3) Trying AT-mode entry sequence (KEY asserted during reset)')
        enter_at_mode()
        time.sleep_ms(500)
        send_at('AT')

    print('\nDone.')
