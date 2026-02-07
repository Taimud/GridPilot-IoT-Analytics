import requests
import json
import time
import random
import sys
import select

# --- CONFIGURATION ---
BASE_URL = "https://gridpilot-core-default-rtdb.firebaseio.com"
DATA_URL = f"{BASE_URL}/generator_01.json"
CONTROL_URL = f"{BASE_URL}/controls.json"

# --- SYSTEM STATE ---
gen_state = "OFF"
grid_state = "CONNECTED"
water_pump = "OFF"

# --- SIMULATION FLAGS (For the Video) ---
sim_blackout = False  # Forces grid voltage to 0

# --- ASSET VALUES ---
fuel_percent = 90.0
water_level = 48.0
solar_volts = 0.0
gen_voltage = 0
grid_voltage = 220

def get_input():
    """ Checks for keyboard input without stopping the loop (Mac/Linux) """
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.readline().strip().lower()
    return None

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
                    print("📲 APP: START ENGINE")
                    gen_state = "ON"
                elif target == "OFF" and gen_state == "ON":
                    print("📲 APP: STOP ENGINE")
                    gen_state = "OFF"
            
            # 2. GRID COMMAND (Only updates if not in manual blackout mode)
            if 'grid_switch' in cmds and not sim_blackout:
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
        fuel_percent -= 0.02  # Burning fuel
    else:
        # Engine cooling down
        if gen_voltage > 0: gen_voltage -= 10
        else: gen_voltage = 0
        
    # --- WATER PUMP LOGIC ---
    if water_pump == "ON":
        water_level += 0.5  # Filling up
        if water_level > 100: water_level = 100
    else:
        water_level -= 0.01  # Slow usage
        
    # --- SOLAR LOGIC ---
    solar_volts = 48.0 + random.uniform(-2, 2)
    
    # --- GRID LOGIC ---
    if sim_blackout:
        grid_voltage = 0 # Forced Blackout
    elif grid_state == "CONNECTED":
        grid_voltage = 220 + random.randint(-5, 5)
    else:
        grid_voltage = 0  # Manual Isolation

def push_telemetry():
    """ Sends the sensor data back to the Web App """
    status_msg = "System Nominal"
    if gen_state == "ON": status_msg = "Generator Active" # Matches frontend check
    if grid_voltage == 0: status_msg = "⚠️ BLACKOUT - Grid Lost"
    
    payload = {
        "fuel_percent": round(fuel_percent, 1),
        "water_level": int(water_level),
        "solar_battery_volts": round(solar_volts, 1),
        "grid_voltage": grid_voltage,
        "gen_voltage": gen_voltage,
        "gas_weight": 12.5,
        "status_message": status_msg
    }
    try:
        requests.put(DATA_URL, json=payload)
        # Dynamic Print
        sys.stdout.write(f"\r📡 Grid: {grid_voltage}V | Gen: {gen_voltage}V | Fuel: {round(fuel_percent,1)}% | Blackout Mode: {sim_blackout}   ")
        sys.stdout.flush()
    except:
        pass

# --- MAIN LOOP ---
print("--- GRID-PILOT DIRECTOR MODE ONLINE ---")
print("⌨️  CONTROLS: 'b' = BLACKOUT | 't' = THEFT | 'r' = RESET")
print("Waiting for Action...")

while True:
    # 1. Check for Director Input (Keyboard)
    key = get_input()
    if key == 'b':
        sim_blackout = True
        print("\n🚫 SIMULATING BLACKOUT... (Grid Voltage -> 0V)")
    elif key == 't':
        fuel_percent -= 15
        print("\n⚠️ SIMULATING THEFT... (Fuel dropped 15%)")
    elif key == 'r':
        sim_blackout = False
        fuel_percent = 90.0
        print("\n✅ SYSTEM RESET (Grid Restored, Fuel Refilled)")

    # 2. Run Normal Logic
    check_commands()
    simulate_hardware()
    push_telemetry()
    time.sleep(1)