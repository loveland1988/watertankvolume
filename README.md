Disclaimer: This project was 100% vibe-coded with ChatGPT.

## Summary:
This project uses a Raspberry Pi and a couple sensors to run a web server that reports the following in JSON: 
- temperature in Celsius
- temperature in Fahrenheit
- humidity percentage
- distance to water surface in cm
- height of water in cm
- volume of water in a tank with known dimensions
You can then use the output from the web server in Home Assistant.


## Background:
I have a 1200gal water tank which is slowly filled by pumping water from an old well on my property (~10gal every 2hrs).  To avoid stressing (read: running dry) my house well, I exclusively use the water tank for irrigation (garden, new trees, etc).  If my usage is low, then the tank will overflow without manual intervention.  If my usage is high and the tank is drawn too low, I run the risk of burning up the pump that feeds the irrigation system.  So, I needed a reasonably-reliable method for estimating the amount of water in the tank (without physically checking it).


## Hardware Components
- Raspberry Pi Zero 2W (with header)
- HC-SR04 ultrasonic sensor
  - Resistors for voltage divider
    - 330 Ohm resistor
    - 470 Ohm resistor
  - Wiring instructions for HC-SR04 can be found here: https://www.raspberrypi-spy.co.uk/2012/12/ultrasonic-distance-measurement-using-python-part-1/
    - Note: I think I burned up GPIO 23 and/or 24 on my Pi, so my code uses GPIO17 for trig and GPIO22 for echo
- DHT22 temp/humidity sensor (more accurate speed of sound calc and to report temp/humidity)
  - Wiring instructions for DHT22 can be found here: https://www.instructables.com/Raspberry-Pi-Tutorial-How-to-Use-the-DHT-22/


## Files
- watertankvolume.py
  - Creates web server, calculates volume, and reports out the values in JSON
- requirements.txt
  - Python packages required
- watertank.service (sets up daemon so program runs at boot)
  - This should be placed in /etc/systemd/system/
  - You will need to update this to reflect the location of your virtual environment and the watertankvolume.py file
- jankyrig.jpeg - picture of my test setup
- Home Assistant Card.png

## Set up the Pi
1. Flash SD card with Raspberry Pi OS - I used the latest headless 64-bit (non-desktop) vesion
2. Wire up your rig (see links above for instructions and note the different GPIOs used in this project for the ultrasonic sensor)
3. SSH into your Raspberry Pi
-   `ssh <username>@<ip address>`
4. Create a virtual environment
-   `sudo python3 -m venv venv`
5. Activate virtual environment
-   `source venv/bin/activate`
6. Install python packages
-   `pip install -r requirements.txt`
7. Test program
-   `python3 watertankvolume.py`
  - In your browser, go to: `http://<ip address of pi>:5000/sensor`
8. If the program is working, you can now copy over the service file and activate it by reloading the daemon
-   `sudo cp watertank.service /etc/systemd/system/`
-   `sudo systemctl daemon-reload`
9. If wifi connection to pi is spotty, deactivate power save mode
  - Deactivate power save mode
    -   `sudo iwconfig wlan0 power off`
  - Keep power save mode off persistent through reboots

    ```Create file
    sudo nano /etc/NetworkManager/conf.d/default-wifi-powersave-on.conf
    ```

    ```Paste into the file
    [connection]
    wifi.powersave = 2
    ```

## Some other notes
- 
- 

## How it Works
1. The DHT22 measures the current temperature (and humidity)
2. The RPi calculates the speed of sound (m/s): v<sub>sound</sub> = 331.3 + 0.606 * temperature<sub>Celsius</sub>
3. The RPi tells the HC-SR04 to send an ultrasonic pulse through the trigger pin which is reflected and picked up by the echo pin.
4. The RPi measures the travel time between the trigger and echo (and divides by 2 since the sound traveled to the water and then back)
5. The RPi calculates the distance: d =  v<sub>sound</sub> * (travel time/2)
6. The water tank dimensions and shape (cylinder in my case) are known, so if the tank is full, the distance would be ~0.  We can calculate the volume of water as volume = pi * r<sub>tank</sub><sup>2</sup> * (h<sub>tank</sub> - d).  As of 9/15/25, this part of the program is approximate as I am only using estimated dimensions.
7. The python script averages five measurements and then reports out the values for {temperature_c, temperature_f, humidity_percent, distance_cm, waterheight_cm, volume_gallons} in JSON via the web server.

## Home Assistant
1. Update your configuration.yaml
  - I did this by SSHing into my HA VM, but I think there are other ways to do it
  - `nano /root/config/configuration.yaml`
    ```
    sensor:
      - platform: rest
        name: "Water Tank Raw"
        resource: "http://<ip address of RPi>:5000/sensor"
        json_attributes:
          - distance_cm
          - water_height_cm
          - volume_gallons
          - temperature_c
          - temperature_f
          - humidity_percent
        value_template: "{{ value_json.volume_gallons }}"
        scan_interval: 15

    template:
      - sensor:
          - name: "Water Tank Volume"
            unit_of_measurement: "gal"
            state: "{{ state_attr('sensor.water_tank_raw', 'volume_gallons') | round(0) }}"
          - name: "Water Tank Distance"
            unit_of_measurement: "cm"
            state: "{{ state_attr('sensor.water_tank_raw', 'distance_cm') | round(1) }}"
          - name: "Water Tank Water Height"
            unit_of_measurement: "cm"
            state: "{{ state_attr('sensor.water_tank_raw', 'water_height_cm') | round(1) }}"
          - name: "Water Tank Temperature"
            unit_of_measurement: "°F"
            state: "{{ state_attr('sensor.water_tank_raw', 'temperature_f') | round(1) }}"
          - name: "Water Tank Humidity"
            unit_of_measurement: "%"
            state: "{{ state_attr('sensor.water_tank_raw', 'humidity_percent') | round(1) }}"
      ```
2. Add a card to your dashboard that calls on the sensor added in the step above
  - I used a gauge card for the volume
    ```
    type: gauge
    entity: sensor.water_tank_volume
    max: 1200
    min: 200
    unit: Gallons
    name: Workshop Water Tank
    needle: false
    severity:
      green: 800
      yellow: 500
      red: 200
    ```
  - And an entities card for the other values
    ```
    type: entities
    title: Water Tank
    entities:
      - entity: sensor.water_tank_distance
        name: Distance
      - entity: sensor.water_tank_temperature
        name: Temperature
      - entity: sensor.water_tank_humidity
    ```

And that's pretty much it!
