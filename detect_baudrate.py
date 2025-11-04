from machine import UART, Pin
import time

# Common baud rates to test
baud_rates = [9600, 38400, 57600, 115200]

def test_baud_rate(baud):
    uart = UART(0, baudrate=baud, tx=Pin(0), rx=Pin(1), bits=8, parity=None, stop=1)
    print(f"\nTesting baud rate: {baud}")
    
    # Clear any existing data
    uart.read()
    
    timeout = time.time() + 5  # 5 second timeout
    while time.time() < timeout:
        if uart.any():
            data = uart.read()
            if data:
                print(f"Received at {baud} baud:")
                print("Raw bytes:", [hex(b) for b in data])
                try:
                    text = data.decode('ascii')
                    print("As text:", text)
                    print("ASCII values:", [ord(c) for c in text])
                except:
                    print("Could not decode as ASCII")
            return True
    return False

print("Starting baudrate detection...")
print("Please send some text from your Bluetooth device")
print("Testing each baud rate for 5 seconds...")

for baud in baud_rates:
    if test_baud_rate(baud):
        print(f"\nSuccessfully received data at {baud} baud!")
        print(f"This is likely the correct baud rate.")
    time.sleep(1)  # Pause between tests

print("\nTest completed. If no clear successful rate was found, try:")
print("1. Checking your HC-05 module's configuration")
print("2. Verifying the physical connections")
print("3. Making sure your Bluetooth device is properly paired")