import json
from machine import Pin
import network
import time
import ujson
import urequests

# Sensitive globals to be defined later
env_vars = {
    "WLAN_SSID": None,
    "WLAN_PW": None,
}
led = None

def load_env():
    with open("env.json") as json_file:
        env_dict = json.load(json_file)
        for k in env_vars.keys():
            try:
                env_vars[k] = env_dict[k]
            except KeyError:
                print('ERROR: Key "{}" does not exist in env.json'.format(k))

def setup_network():
    """
    Connect to network
    Ideally this happens just once to reduce stress on network access point
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("connecting to network...")
        wlan.connect(env_vars["WLAN_SSID"], env_vars["WLAN_PW"])
        while not wlan.isconnected():
            pass
    device_ip = wlan.ifconfig()[0]
    print("Device IP:", device_ip)

class Button:
    def __init__(self, gpio_num, name, up_callback = None, down_callback = None):
        self.is_pressed = False
        self.name = name
        self.gpio_num = gpio_num
        self.up_callback = up_callback
        self.down_callback = down_callback
        self.pin = Pin(gpio_num, Pin.IN, Pin.PULL_UP)
        self.pin.irq(
            trigger=Pin.IRQ_FALLING|Pin.IRQ_RISING,
            handler=self.callback)
        self.callback(self.pin)

    def callback(self, pin):
        if pin.value() == 1:
            if self.is_pressed == True and not self.down_callback is None:
                self.down_callback()
            self.is_pressed = False
        else:
            if self.is_pressed == False and not self.up_callback is None:
                self.up_callback()
            self.is_pressed = True

def up_callback():
    print("Button Pressed")
    # Turn on LED
    led.value(0)

    # request_url = 'https://2b9270e7-d007-4109-8771-20bc63f22ada.mock.pstmn.io'
    request_url = 'http://digibp-buendner-nusstorte.herokuapp.com/engine-rest/message'
    post_data = ujson.dumps({'messageName': 'beerReceived'})
    header_data = {"Content-Type": "application/json", "accept": "*/*", "accept-encoding": "gzip, deflate"}
    try:
        response = urequests.post(request_url, data=post_data, headers=header_data)
    # For some reason, the response from Camunda is not accepted by urequests, but it still works, so just ignore the error.
    except ValueError:
        pass
    
    time.sleep(3)
    
    # Turn off LED
    led.value(1)

def setup_pins():
    global led
    # Set up LED
    led = Pin(2, Pin.OUT)
    led.value(1)
    # Set up Button
    Button(12, 'name of button', up_callback, None)

load_env()
setup_network()
setup_pins()