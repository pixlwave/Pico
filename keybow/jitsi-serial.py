# jitsi shortcuts over serial for keybow 2040

# drop the keybow2040.py file into your `lib` folder on your `CIRCUITPY` drive.

import board
import usb_cdc
from keybow2040 import Keybow2040

# setup Keybow
i2c = board.I2C()
keybow = Keybow2040(i2c)
keys = keybow.keys

# setup serial
serial = usb_cdc.console

# the keyboard characters in order
keymap = [
    " ",    # push to talk
    "3",    # focus on person 3
    "0",    # focus on me
    "m",    # toggle mic
    
    "a",    # call quality
    "4",    # focus on person 4
    "1",    # focus on person 1
    "v",    # toggle video
    
    "t",    # speaker stats
    "5",    # focus on person 5
    "2",    # focus on person 2
    "d",    # screen sharing
    
    "s",    # full screen
    "w",    # tile view
    "f",    # video thumbnails
    "r"     # raise hand
]

# the key colours in order
rgb = [
    (255, 127, 0),    # push to talk
    (255, 63, 63),    # focus on person 3
    (255, 63, 63),    # focus on me
    (0, 255, 0),      # toggle mic
    
    (63, 255, 63),    # call quality
    (255, 63, 63),    # focus on person
    (255, 63, 63),    # focus on person
    (255, 0, 0),      # toggle video
    
    (63, 255, 63),    # speaker stats
    (255, 63, 63),    # focus on person 5
    (255, 63, 63),    # focus on person 2
    (0, 255, 255),    # screen sharing
    
    (0, 0, 255),      # full screen
    (255, 255, 0),    # tile view
    (255, 255, 0),    # video thumbnails
    (255, 255, 255)   # raise hand
]

keyDownCommand = "!1"
keyUpCommand = "!0"
terminator = ";"

# set initial colours and attach handler functions to the keys
for key in keys:
    # default colour
    key.set_led(*rgb[key.number])
    
    @keybow.on_press(key)
    def press_handler(key):
        keycode = keymap[key.number]
        serial.write(bytes(keyDownCommand + keycode + terminator, "ascii"))
        serial.flush()
        key.set_led(255, 255, 255)
    
    # release handler
    @keybow.on_release(key)
    def release_handler(key):
        keycode = keymap[key.number]
        serial.write(bytes(keyUpCommand + keycode + terminator, "ascii"))
        serial.flush()
        key.set_led(*rgb[key.number])

while True:
    # always remember to call keybow.update()!
    keybow.update()
