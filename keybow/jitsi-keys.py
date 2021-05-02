# jitsi shortcuts for keybow 2040

# based on the hid-keys-simple.py example by Sandy Macdonald

# drop the keybow2040.py file into your `lib` folder on your `CIRCUITPY` drive.
# NOTE! requires the adafruit_hid CircuitPython library also!

import board
from keybow2040 import Keybow2040

import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

# setup Keybow
i2c = board.I2C()
keybow = Keybow2040(i2c)
keys = keybow.keys

# setup keyboard and layout
keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)

# the keycodes in order
keymap = [
    Keycode.SPACE,    # push to talk
    Keycode.THREE,    # focus on person 3
    Keycode.ZERO,     # focus on me
    Keycode.M,        # toggle mic
    
    Keycode.A,        # call quality
    Keycode.FOUR,     # focus on person 4
    Keycode.ONE,      # focus on person 1
    Keycode.V,        # toggle video
    
    Keycode.T,        # speaker stats
    Keycode.FIVE,     # focus on person 5
    Keycode.TWO,      # focus on person 2
    Keycode.D,        # screen sharing
    
    Keycode.S,        # full screen
    Keycode.W,        # tile view
    Keycode.F,        # video thumbnails
    Keycode.R         # raise hand
]

# the key colours in order
rgb = [
    (255, 127, 0),    # push to talk
    (255, 127, 127),  # focus on person 3
    (255, 127, 127),  # focus on me
    (0, 255, 0),      # toggle mic
    
    (127, 0, 255),    # call quality
    (255, 127, 127),  # focus on person
    (255, 127, 127),  # focus on person
    (255, 0, 0),      # toggle video
    
    (64, 64, 64),     # speaker stats
    (255, 127, 127),  # focus on person 5
    (255, 127, 127),  # focus on person 2
    (0, 255, 255),    # screen sharing
    
    (0, 0, 255),      # full screen
    (255, 255, 0),    # tile view
    (255, 255, 0),    # video thumbnails
    (255, 255, 255)   # raise hand
]

# set initial colours and attach handler functions to the keys
for key in keys:
    # default colour
    key.set_led(*rgb[key.number])
    
    if key.number == 0:
        @keybow.on_press(key)
        def press_handler(key):
            keycode = keymap[key.number]
            keyboard.press(keycode)
            key.set_led(255, 255, 255)
        
        # release handler
        @keybow.on_release(key)
        def release_handler(key):
            keycode = keymap[key.number]
            keyboard.release(keycode)
            key.set_led(*rgb[key.number])
    else:
        # press handler
        @keybow.on_press(key)
        def press_handler(key):
            keycode = keymap[key.number]
            keyboard.send(keycode)
            key.set_led(255, 255, 255)
    
        # release handler
        @keybow.on_release(key)
        def release_handler(key):
            key.set_led(*rgb[key.number])

while True:
    # always remember to call keybow.update()!
    keybow.update()
