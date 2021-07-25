# basic midi support for keybow
# keys coloured to match a jitsi shortcut layout

# based on the midi-keys.py example by Sandy Macdonald

import board
from keybow2040 import Keybow2040

import usb_midi
import adafruit_midi
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from adafruit_midi.start import Start
from adafruit_midi.stop import Stop

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

isActive = False


def color_for_key(key):
    if isActive:
        return rgb[key.number]
    else:
        return (0, 0, 0)


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
        if not isActive:
            isActive = True
            update_idle_colors()
    elif type(message) is Stop:
        if isActive:
            isActive = False
            update_idle_colors()
    
    # always remember to call keybow.update()!
    keybow.update()
