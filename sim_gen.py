import requests
import json
import time
import random

# CONFIG - CONNECT TO YOUR DATABASE
BASE_URL = "https://gridpilot-core-default-rtdb.firebaseio.com"
DATA_URL = f"{BASE_URL}/generator_01.json"
COMMAND_URL = f"{BASE_URL}/commands/generator_01.json"
MARKET_URL = f"{BASE_URL}/market_settings.json"

# NIGERIA-SPECIFIC DEFAULTS (These will be updated by the sync function)
DIESEL_PRICE_PER_LITER = 1350  
LITERS_PER_HOUR = 4.2          
CURRENCY = "₦"

system_state = "ON"
current_temp = 25
runtime_seconds = 0

def sync_market_data():
    """Pulls the latest Diesel price and Burn Rate from your Settings page"""
    global DIESEL_PRICE_PER_LITER, LITERS_PER_HOUR
    try:
        res = requests.get(MARKET_URL)
        if res.status_code == 200:
            market = res.json()
            if market:
                DIESEL_PRICE_PER_LITER = float(market.get('diesel_price', 1350))
                LITERS_PER_HOUR = float(market.get('burn_rate', 4.2))
    except Exception as e:
        print(f"Sync Error: {e}")

def check_safety_and_commands():
    global system_state, current_temp
    
    # --- AUTO-PILOT SAFETY LOGIC ---
    if system_state == "ON" and current_temp >= 100:
        print(f"\n [AUTO-PILOT] 🚨 CRITICAL OVERHEAT ({current_temp}C)! EMERGENCY SHUTDOWN...")
        requests.put(COMMAND_URL, json="STOP")
    
    try:
        res = requests.get(COMMAND_URL)
        if res.status_code == 200:
            cmd = res.json()
            if cmd == "STOP": system_state = "OFF"
            elif cmd == "START": system_state = "ON"
    except: pass

def get_enterprise_data():
    global system_state, current_temp, runtime_seconds
    
    # Simulating Fuel consumption
    fuel_pct = max(0, 90 - (runtime_seconds / 60)) 
    
    # DYNAMIC COST CALCULATION (Using synced Market Data)
    hours_run = runtime_seconds / 3600
    liters_used = hours_run * LITERS_PER_HOUR
    total_cost_naira = round(liters_used * DIESEL_PRICE_PER_LITER, 2)
    
    if system_state == "ON" and fuel_pct > 0:
        minutes_remaining = fuel_pct  
        runtime_seconds += 2 
    else:
        minutes_remaining = 0

    if system_state == "OFF":
        oil = 0
        if current_temp > 30: current_temp -= 2 
    else:
        oil = random.randint(45, 55)
        if current_temp < 105: current_temp += 4 
    
    health = 100
    if current_temp > 90: health -= 30
    if fuel_pct < 20: health -= 20
    if oil < 30 and system_state == "ON": health -= 40

    return {
        "fuel_percent": round(fuel_pct, 1),
        "engine_temp": current_temp,
        "oil_pressure": oil,
        "health_score": max(0, health),
        "total_cost": f"{CURRENCY}{total_cost_naira:,.2f}", 
        "system_state": system_state,
        "grid_voltage": random.randint(210, 230) if system_state == "ON" else 0,
        "status_message": f"TTE: {int(minutes_remaining)} mins" if system_state == "ON" else "SYSTEM IDLE",
        "solar_battery_volts": round(random.uniform(48.5, 53.5), 1),
        "water_level": random.randint(40, 95),
        "region": "Lagos, NG"
    }

print("--- GRID-PILOT AFRICA ENTERPRISE CORE ONLINE ---")

while True:
    sync_market_data() # Step 1: Check if prices changed on the web
    check_safety_and_commands() # Step 2: Check for STOP/START
    data = get_enterprise_data() # Step 3: Run the simulation
    requests.put(DATA_URL, json=data) # Step 4: Upload to Cloud
    
    state_icon = "🟢" if system_state == "ON" else "🔴"
    print(f" {state_icon} Fuel: {data['fuel_percent']}% | Cost: {data['total_cost']} | Rate: {LITERS_PER_HOUR}L/h")
    time.sleep(2)