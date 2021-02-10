# usb midi step sequencer for raspberry pi pico
# written for circuitpython v6.2.0
# requires the following libs:
# - adafruit_bus_device
# - adafruit_dotstar
# - adafruit_midi

import board
import time
import random

# led control
import adafruit_dotstar
from digitalio import DigitalInOut, Direction

# button access
import busio
from adafruit_bus_device.i2c_device import I2CDevice

# midi comms
import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff


# led setup
cs = DigitalInOut(board.GP17)
cs.direction = Direction.OUTPUT
cs.value = 0
pixels = adafruit_dotstar.DotStar(board.GP18, board.GP19, 16,
                                  brightness=0.5, auto_write=True)

# button setup
i2c = busio.I2C(board.GP5, board.GP4)
device = I2CDevice(i2c, 0x20)

# midi setup
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)


# enums
class ButtonState:
    PRESSED = 1
    LONGPRESSED = 2
    RELEASED = 3


class ButtonMode:
    PATTERN = 1
    NOTE_CHOOSER = 2
    WAIT = 3


class Color:
    KICK = (127, 0, 0)
    SNARE = (0, 127, 0)
    CLAP = (127, 0, 127)
    HIHAT = (0, 127, 127)
    TOM = (127, 63, 0)
    CYMBOL = (0, 0, 127)
    
    MARKER = (16, 16, 16)
    NOTE = (255, 255, 255)
    OFF = (0, 0, 0)


def halfColor(color):
    return tuple([int(0.1 * value) for value in color])


# variables
step = 0
note = 0
pattern = [[False] * 16 for _ in range(16)]
button_map = [12, 13, 14, 15, 8, 9, 10, 11, 4, 5, 6, 7, 0, 1, 2, 3]
note_colors = [Color.KICK, Color.SNARE, Color.SNARE, Color.CLAP,
               Color.SNARE, Color.TOM, Color.HIHAT, Color.TOM,
               Color.HIHAT, Color.TOM, Color.HIHAT, Color.TOM,
               Color.TOM, Color.CYMBOL, Color.TOM, Color.CYMBOL]
note_dimmed_colors = [halfColor(color) for color in note_colors]
dim_notes = [False] * 16

button_mode = ButtonMode.PATTERN
last_button_states = [0] * 16
last_button_pressed_times = [None] * 16


def read_button_states():
    pressed = [0] * 16
    with device:
        device.write(bytes([0x0]))
        result = bytearray(2)
        device.readinto(result)
        b = result[0] | result[1] << 8
        for i in range(16):
            if not (1 << i) & b:
                pressed[i] = 1
            else:
                pressed[i] = 0
    return pressed


def wait(delay):
    update_leds()
    
    global button_mode
    global last_button_states
    global last_button_pressed_times
    
    now = time.monotonic()
    while time.monotonic() < now + delay:
        button_states = read_button_states()
        
        if button_mode == ButtonMode.WAIT:
            if all(state == 0 for state in button_states):
                button_mode = ButtonMode.PATTERN
        else:
            for i in range(16):
                if button_states[i] == 1 and last_button_states[i] == 0:
                    last_button_pressed_times[i] = now
                    buttonPress(i, ButtonState.PRESSED, now)
                elif button_states[i] == 1:
                    if last_button_pressed_times[i] + 0.5 < now:
                        buttonPress(i, ButtonState.LONGPRESSED, now)
                elif button_states[i] == 0 and last_button_states[i] == 1:
                    buttonPress(i, ButtonState.RELEASED, now)
                    last_button_pressed_times[i] = None
        
        last_button_states = button_states
        time.sleep(0.001)


def buttonPress(index, state, time):
    global note
    global pattern
    global button_mode
    global dim_notes
    
    if button_mode == ButtonMode.NOTE_CHOOSER:
        if state == ButtonState.PRESSED:
            note = button_map[index]
            button_mode = ButtonMode.WAIT
    elif button_mode == ButtonMode.PATTERN:
        if index == 15:
            if state == ButtonState.LONGPRESSED:
                for i in range(16):
                    dim_notes[i] = any(n for n in pattern[button_map[i]])
                button_mode = ButtonMode.NOTE_CHOOSER
            elif state == ButtonState.RELEASED:
                pattern[note][15] = not pattern[note][15]
        elif index == 3 and state == ButtonState.LONGPRESSED:
            reset()
        else:
            if state == ButtonState.PRESSED:
                pattern[note][index] = not pattern[note][index]


def playNotes(step):
    for i in range(16):
        if pattern[i][step]:
            midi.send(NoteOn(36 + i, 120))


def stopNotes(step):
    for i in range(16):
        if pattern[i][step]:
            midi.send(NoteOff(36 + i, 120))


def reset_notes():
    for i in range(16):
        midi.send(NoteOff(36 + i, 120))


def reset():
    global note
    global pattern
    
    note = 0
    pattern = [[False] * 16 for _ in range(16)]


def update_leds():
    if button_mode == ButtonMode.PATTERN:
        for i in range(16):
            is_armed = pattern[note][i]
            if i == step:
                pixels[i] = Color.NOTE if is_armed else Color.MARKER
            else:
                pixels[i] = note_colors[note] if is_armed else Color.OFF
    else:
        for i in range(16):
            if dim_notes[i]:
                pixels[i] = note_colors[button_map[i]]
            else:
                pixels[i] = note_dimmed_colors[button_map[i]]


# midi panic for script reloading
reset_notes()

# main loop
while True:
    stopNotes(step)
    step = (step + 1) % 16
    playNotes(step)
    wait(0.125)
