# basic midi support for keybow
# keys coloured to match a custom shortcut layout

# based on the midi-keys.py example by Sandy Macdonald

import board
from keybow2040 import Keybow2040

import usb_midi
import adafruit_midi
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from adafruit_midi.start import Start
from adafruit_midi.stop import Stop
from adafruit_midi.midi_continue import Continue


class Color:
    RED = (255, 0, 0)
    ORANGE = (255, 127, 0)
    YELLOW = (255, 255, 0)
    GREEN = (0, 255, 0)
    MINT = (63, 255, 63)
    CYAN = (0, 255, 255)
    BLUE = (0, 0, 255)
    PINK = (255, 63, 63)
    
    WHITE = (255, 255, 255)
    OFF = (0, 0, 0)


# set keybow
i2c = board.I2C()
keybow = Keybow2040(i2c)
keys = keybow.keys

# setup midi
midi = adafruit_midi.MIDI(midi_in=usb_midi.ports[0], in_channel=0,
                          midi_out=usb_midi.ports[1], out_channel=0)
start_note = 36
keymap = [
    0, 4, 8, 12,
    1, 5, 9, 13,
    2, 6, 10, 14,
    3, 7, 11, 15
]
velocity = 127

# the key colours in order for Jitsi
rgbMainLayer = [
    Color.YELLOW,     # reaction - clap
    Color.YELLOW,     # reaction - laugh
    Color.YELLOW,     # reaction - thumbs up
    Color.MINT,       # function #1
    
    Color.GREEN,      # toggle video
    Color.CYAN,       # screen sharing
    Color.YELLOW,     # reaction - surprise
    Color.MINT,       # function #2
    
    Color.ORANGE,     # toggle mic
    Color.PINK,       # toggle thumbnails
    Color.YELLOW,     # raise hand
    Color.MINT,       # function #3
    
    Color.RED,        # push to talk
    Color.PINK,       # tile view
    Color.BLUE,       # end call
    Color.WHITE       # special key
]

# the key colours in order for Element
rgbSecondaryLayer = [
    Color.OFF,        # unused
    Color.OFF,        # unused
    Color.OFF,        # unused
    Color.MINT,       # function #1
    
    Color.GREEN,      # toggle video
    Color.OFF,        # unused
    Color.OFF,        # unused
    Color.MINT,       # function #2
    
    Color.ORANGE,     # toggle mic
    Color.OFF,        # unused
    Color.OFF,        # unused
    Color.MINT,       # function #3
    
    Color.OFF,        # unused
    Color.OFF,        # unused
    Color.BLUE,       # end call
    Color.WHITE       # special key
]

rgb = [rgbMainLayer, rgbSecondaryLayer]

isActive = False
layer = 0


def color_for_key(key):
    if isActive:
        return rgb[layer][key.number]
    else:
        return Color.OFF


# attach handlers to keys
for key in keys:
    # default colour
    key.set_led(*color_for_key(key))
    
    # If pressed, send a MIDI note on command and light key.
    @keybow.on_press(key)
    def press_handler(key):
        note = start_note + keymap[key.number]
        midi.send(NoteOn(note, velocity))
        key.set_led(255, 255, 255)

    # If released, send a MIDI note off command and turn off LED.
    @keybow.on_release(key)
    def release_handler(key):
        note = start_note + keymap[key.number]
        midi.send(NoteOff(note, 0))
        key.set_led(*color_for_key(key))


def update_idle_colors():
    for key in keys:
        if key.get_state() == 0:
            key.set_led(*color_for_key(key))


while True:
    message = midi.receive()
    
    if type(message) is Start:
        if not isActive or not layer == 0:
            layer = 0
            isActive = True
            update_idle_colors()
    elif type(message) is Continue:
        if not isActive or not layer == 1:
            layer = 1
            isActive = True
            update_idle_colors()
    elif type(message) is Stop:
        if isActive:
            isActive = False
            update_idle_colors()
    
    # always remember to call keybow.update()!
    keybow.update()
