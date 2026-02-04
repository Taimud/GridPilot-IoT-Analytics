import requests
import json
import time
import random
import datetime

# --- CONFIGURATION ---
BASE_URL = "https://gridpilot-core-default-rtdb.firebaseio.com"
DATA_URL = f"{BASE_URL}/generator_01.json"
CONTROL_URL = f"{BASE_URL}/controls.json" # New Control Channel

# --- HARDWARE STATE ---
gen_state = "OFF"     # The engine status
grid_state = "CONNECTED" 
water_pump = "OFF"

# Asset Values
fuel_percent = 90.0
water_level = 48.0
solar_volts = 0.0
gen_voltage = 0
grid_voltage = 220

def check_commands():
    """ Listens to the Web App for instructions """
    global gen_state, grid_state, water_pump
    try:
        res = requests.get(CONTROL_URL)
        if res.status_code == 200 and res.json():
            cmds = res.json()
            
            # 1. GENERATOR COMMAND
            if 'generator' in cmds:
                target = cmds['generator'].get('state', 'OFF')
                if target == "ON" and gen_state == "OFF":
                    print("📲 COMMAND RECEIVED: START ENGINE")
                    gen_state = "ON"
                elif target == "OFF" and gen_state == "ON":
                    print("📲 COMMAND RECEIVED: STOP ENGINE")
                    gen_state = "OFF"

            # 2. GRID COMMAND
            if 'grid_switch' in cmds:
                target = cmds['grid_switch'].get('state', 'CONNECTED')
                grid_state = target

            # 3. WATER COMMAND
            if 'water_pump' in cmds:
                water_pump = cmds['water_pump'].get('state', 'OFF')

    except Exception as e:
        print(f"Signal Error: {e}")

def simulate_hardware():
    global fuel_percent, water_level, gen_voltage, solar_volts, grid_voltage

    # --- GENERATOR LOGIC ---
    if gen_state == "ON":
        # Engine revving up
        if gen_voltage < 220: gen_voltage += 20 
        else: gen_voltage = random.randint(220, 230)
        fuel_percent -= 0.02 # Burning fuel
    else:
        # Engine cooling down
        if gen_voltage > 0: gen_voltage -= 10
        else: gen_voltage = 0

    # --- WATER PUMP LOGIC ---
    if water_pump == "ON":
        water_level += 0.5 # Filling up
        if water_level > 100: water_level = 100
    else:
        water_level -= 0.01 # Slow usage

    # --- SOLAR LOGIC ---
    # Sun is up (simple simulation)
    solar_volts = 48.0 + random.uniform(-2, 2)

    # --- GRID LOGIC ---
    if grid_state == "CONNECTED":
        grid_voltage = 220 + random.randint(-5, 5)
    else:
        grid_voltage = 0 # Isolated

def push_telemetry():
    """ Sends the sensor data back to the Web App """
    status_msg = "System Nominal"
    if gen_state == "ON": status_msg = "Engine Running"
    if grid_state == "ISOLATED": status_msg = "Grid Disconnected"

    payload = {
        "fuel_percent": round(fuel_percent, 1),
        "water_level": int(water_level),
        "solar_battery_volts": round(solar_volts, 1),
        "grid_voltage": grid_voltage,
        "gen_voltage": gen_voltage, # Sending Gen Voltage now
        "gas_weight": 12.5, # Static for now
        "status_message": status_msg
    }
    
    try:
        requests.put(DATA_URL, json=payload)
        print(f"📡 STATUS: Gen={gen_state} ({gen_voltage}V) | Grid={grid_state} | Water={water_pump}")
    except:
        pass

# --- MAIN LOOP ---
print("--- GRID-PILOT HARDWARE CONTROLLER ONLINE ---")
print("Waiting for Web Commands...")

while True:
    check_commands()    # 1. Listen for Web
    simulate_hardware() # 2. React to physics
    push_telemetry()    # 3. Update Web
    time.sleep(1)