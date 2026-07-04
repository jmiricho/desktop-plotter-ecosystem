import serial
import time
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow your frontend HTML file to talk to this backend server safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Hardware Configuration ---
SERIAL_PORT = 'COM3'  # Update this to match your physical port later
BAUD_RATE = 115200
device = None

def init_serial():
    global device
    try:
        print(f"Connecting to hardware on {SERIAL_PORT}...")
        device = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2) # Microcontroller reboot delay
        print("Hardware serial link established.")
    except Exception as e:
        print(f"Serial warning: Hardware not connected. Running in Simulation Mode. ({e})")
        device = None

init_serial()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Manages the live real-time data link between the web UI and the machine."""
    await websocket.accept()
    print("Frontend dashboard connected to WebSocket server.")
    
    try:
        while True:
            # Wait for incoming command messages sent from the browser buttons
            client_message = await websocket.receive_text()
            print(f"Received from UI: {client_message}")
            
            if client_message == "CMD_HOME":
                await websocket.send_text("STATUS: Homing sequence initiated...")
                if device:
                    device.write(b"G28\n") # Real G-code command for homing
                    # Simulate waiting for hardware handshake line response
                    await asyncio.sleep(1.5) 
                else:
                    await asyncio.sleep(1.5) # Simulated motion time
                await websocket.send_text("CONSOLE: X-axis hit limit switch.")
                await websocket.send_text("CONSOLE: Y-axis hit limit switch.")
                await websocket.send_text("STATUS: READY")
                
            elif client_message == "CMD_ESTOP":
                if device:
                    device.write(b"ESTOP\n")
                await websocket.send_text("STATUS: ALARM LOCKED")
                await websocket.send_text("CONSOLE: [CRITICAL] Hardware E-STOP triggered via Web UI!")
                
            elif client_message == "CMD_STREAM":
                await websocket.send_text("STATUS: RUNNING")
                coords = ["X10 Y20", "X30 Y45", "X0 Y0"]
                for pt in coords:
                    await websocket.send_text(f"CONSOLE: Streaming coordinate target: {pt}")
                    if device:
                        device.write(f"G01 {pt}\n".encode())
                        # Wait for microcontroller to respond with "OK"
                    await asyncio.sleep(0.8)
                await websocket.send_text("STATUS: READY")
                
    except WebSocketDisconnect:
        print("Frontend dashboard disconnected.")