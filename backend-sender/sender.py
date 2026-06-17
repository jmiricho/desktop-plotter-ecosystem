import serial
import time
import sys

# --- Configuration Parameters ---
# Change 'COM3' to match whichever port your microcontroller plugs into
SERIAL_PORT = 'COM3' 
BAUD_RATE = 115200

def establish_link():
    """Initializes the serial connection to the microcontroller."""
    try:
        print(f"Connecting to machine on {SERIAL_PORT} at {BAUD_RATE} baud...")
        # Open serial port with a 2-second readout timeout
        device = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        time.sleep(2) # Crucial: Wait for microcontroller to reboot after connection
        print("Connection established successfully!")
        return device
    except serial.SerialException as e:
        print(f"Error: Could not open port {SERIAL_PORT}. Is the machine plugged in?")
        print(f"Details: {e}")
        sys.exit(1)

def stream_command(device, command):
    """Sends a single coordinate command string and waits for a hardware handshake response."""
    clean_command = command.strip()
    if not clean_command:
        return

    print(f"Sending: {clean_command}")
    # Encode string to bytes and send over the wire with a trailing newline character
    device.write(f"{clean_command}\n".encode('utf-8'))

    # --- The Handshake Protocol Loop ---
    while True:
        if device.in_waiting > 0:
            # Read line from hardware, decode from bytes to string, and strip white space
            response = device.readline().decode('utf-8').strip()
            print(f"Machine Response: {response}")

            # Check if firmware processed the instruction successfully
            if "OK" in response:
                break
            # Check if firmware is trapped in an Emergency Alarm state
            elif "ALARM" in response:
                print("!! CRITICAL HARDWARE ALARM DETECTED !! Stream halted.")
                sys.exit(1)

if __name__ == '__main__':
    # Test dataset simulating coordinate targets
    simulated_coordinates = [
        "G01 X10.5 Y20.0",
        "G01 X30.0 Y45.2",
        "G01 X0.0 Y0.0"
    ]

    # Run connection pipeline
    machine = establish_link()

    print("\n--- Starting Command Stream ---")
    for cmd in simulated_coordinates:
        stream_command(machine, cmd)
        time.sleep(0.5) # Short observational pacing delay

    machine.close()
    print("Stream completed. Port closed safely.")