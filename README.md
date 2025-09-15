Disclaimer: This project was 100% vibe-coded with ChatGPT.

## Summary:
This project uses a Raspberry Pi and a couple sensors to run a web server that reports the following in JSON: 
- current volume of water (or any liquid, I guess) in a tank with known dimensions
- Temperature
- Humidity
- Distance from sensor to water surface
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
  - Creates web server, calculates volume, and reports temp and humidity (and distance to water surface)
- watertank.service (sets up daemon so program runs at boot)
  - This should be placed in /etc/systemd/system/
  - You will need to update this to reflect the location of your virtual environment and the watertankvolume.py file

## How To Use
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

`sudo nano /etc/NetworkManager/conf.d/default-wifi-powersave-on.conf`

```
#Paste the next 2 lines into the editor

[connection]
wifi.powersave = 2
```

## Some other notes
- 
- 
