#!/usr/bin/python3
from flask import Flask, jsonify
import time, statistics, math
import RPi.GPIO as GPIO
import board, adafruit_dht

app = Flask(__name__)

# --- DHT22 Setup ---
dht = adafruit_dht.DHT22(board.D4)

# --- Ultrasonic Setup ---
GPIO.setmode(GPIO.BCM)
GPIO_TRIGGER = 17
GPIO_ECHO = 22
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

# --- Tank dimensions (cm) ---
TANK_HEIGHT_CM = 182.88
TANK_RADIUS_CM = 91.44

# --- Store last good values ---
last_values = {
    "temperature_c": 20.0,
    "temperature_f": 68.0,
    "humidity_percent": 0.0,
    "distance_cm": None,
    "water_height_cm": None,
    "volume_gallons": None,
}

def measure_distance():
    # Try to read temperature + humidity
    try:
        temperature_c = dht.temperature
        humidity = dht.humidity
        if temperature_c is not None:
            last_values["temperature_c"] = temperature_c
            last_values["temperature_f"] = (temperature_c * 9/5) + 32
        if humidity is not None:
            last_values["humidity_percent"] = humidity
    except RuntimeError:
        # Keep last good values if sensor read fails
        pass

    # Speed of sound (cm/s) — temp only
    speedSound = 33100 + (0.6 * last_values["temperature_c"])

    # Trigger pulse
    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    start, stop = time.time(), time.time()

    while GPIO.input(GPIO_ECHO) == 0:
        start = time.time()
    while GPIO.input(GPIO_ECHO) == 1:
        stop = time.time()

    elapsed = stop - start
    distance = (elapsed * speedSound) / 2
    return distance

def calculate_volume(distance_cm):
    water_height = max(TANK_HEIGHT_CM - distance_cm, 0)
    volume_cm3 = math.pi * (TANK_RADIUS_CM ** 2) * water_height
    volume_gal = volume_cm3 / 3785.0
    return water_height, volume_gal

@app.route("/sensor")
def sensor():
    # Take 5 measurements, average
    distances = []
    for _ in range(5):
        try:
            d = measure_distance()
            distances.append(d)
            time.sleep(0.2)
        except Exception:
            pass

    if distances:
        avg_distance = statistics.mean(distances)
        water_height, gallons = calculate_volume(avg_distance)
        last_values["distance_cm"] = avg_distance
        last_values["water_height_cm"] = water_height
        last_values["volume_gallons"] = gallons

    return jsonify(last_values)

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000)
    finally:
        GPIO.cleanup()
        dht.exit()
