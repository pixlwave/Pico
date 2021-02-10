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
midi = [adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=ch) for ch in range(16)]


# enums
class ButtonState:
    PRESSED = 1
    LONGPRESSED = 2
    RELEASED = 3


class ButtonMode:
    PATTERN = 1
    NOTE_CHOOSER = 2
    CHANNEL_CHOOSER = 3
    WAIT = 4


class Color:
    KICK = (127, 0, 0)
    SNARE = (0, 127, 0)
    CLAP = (127, 0, 127)
    HIHAT = (0, 127, 127)
    TOM = (127, 63, 0)
    CYMBOL = (0, 0, 192)
    
    MAJOR = (0, 0, 192)
    SCALE = (0, 63, 63)
    ACCIDENTAL = (63, 0, 63)
    
    CHANNEL = (127, 127, 0)
    DRUM_CHANNEL = (0, 127, 0)
    
    MARKER = (16, 16, 16)
    NOTE = (255, 255, 255)
    NOTE_OFF = (7, 0, 0)
    OFF = (0, 0, 0)


class Note:
    OFF = 0
    ON = 1
    HOLD = 2


def dim_color(color):
    return tuple([int(0.1 * value) for value in color])


# variables
step = 0
note = 0
channel = 0
pattern = [[[Note.OFF] * 16 for _ in range(16)] * 16 for _ in range(16)]
button_map = [12, 13, 14, 15, 8, 9, 10, 11, 4, 5, 6, 7, 0, 1, 2, 3]
next_melody_note = [Note.ON, Note.HOLD, Note.OFF]
next_drum_note = [Note.ON, Note.OFF]

drum_note_colors = [Color.KICK, Color.SNARE, Color.SNARE, Color.CLAP,
                    Color.SNARE, Color.TOM, Color.HIHAT, Color.TOM,
                    Color.HIHAT, Color.TOM, Color.HIHAT, Color.TOM,
                    Color.TOM, Color.CYMBOL, Color.TOM, Color.CYMBOL]
note_dimmed_colors = [dim_color(color) for color in drum_note_colors]
melody_note_colors = [Color.MAJOR, Color.ACCIDENTAL, Color.SCALE, Color.ACCIDENTAL,
                      Color.MAJOR, Color.SCALE, Color.ACCIDENTAL, Color.MAJOR,
                      Color.ACCIDENTAL, Color.SCALE, Color.ACCIDENTAL, Color.SCALE,
                      Color.MAJOR, Color.ACCIDENTAL, Color.SCALE, Color.ACCIDENTAL]
melody_hold_note_colors = [dim_color(color) for color in melody_note_colors]
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
                    button_press(i, ButtonState.PRESSED)
                elif button_states[i] == 1:
                    if last_button_pressed_times[i] + 0.5 < now:
                        button_press(i, ButtonState.LONGPRESSED)
                elif button_states[i] == 0 and last_button_states[i] == 1:
                    button_press(i, ButtonState.RELEASED)
                    last_button_pressed_times[i] = None
        
        last_button_states = button_states
        time.sleep(0.001)


def button_press(index, state):
    global note
    global channel
    global pattern
    global button_mode
    global dim_notes
    
    if button_mode == ButtonMode.NOTE_CHOOSER:
        if state == ButtonState.PRESSED:
            note = button_map[index]
            button_mode = ButtonMode.WAIT
    if button_mode == ButtonMode.CHANNEL_CHOOSER:
        if state == ButtonState.PRESSED:
            note = 0
            channel = button_map[index]
            button_mode = ButtonMode.WAIT
    elif button_mode == ButtonMode.PATTERN:
        if index == 15:
            if state == ButtonState.LONGPRESSED:
                for i in range(16):
                    dim_notes[i] = any(n == Note.ON for n in pattern[channel][button_map[i]])
                button_mode = ButtonMode.NOTE_CHOOSER
            elif state == ButtonState.RELEASED:
                toggle_note(index)
        elif index == 12:
            if state == ButtonState.LONGPRESSED:
                button_mode = ButtonMode.CHANNEL_CHOOSER
            elif state == ButtonState.RELEASED:
                toggle_note(index)
        elif index == 3 and state == ButtonState.LONGPRESSED:
            reset()
        else:
            if state == ButtonState.PRESSED:
                toggle_note(index)


def toggle_note(index):
    global pattern
    if channel == 9:
        pattern[channel][note][index] = next_drum_note[pattern[channel][note][index]]
    else:
        pattern[channel][note][index] = next_melody_note[pattern[channel][note][index]]


def update_notes(lastStep, step):
    for _channel in range(16):
        for _note in range(16):
            if pattern[_channel][_note][step] == Note.ON:
                midi[_channel].send(NoteOn(36 + _note, 120))
            elif pattern[_channel][_note][step] == Note.OFF:
                if pattern[_channel][_note][lastStep] != Note.OFF:
                    midi[_channel].send(NoteOff(36 + _note, 120))


def reset_notes():
    for _channel in range(16):
        for _note in range(16):
            midi[_channel].send(NoteOff(36 + _note, 120))


def reset():
    global note
    global channel
    global pattern
    
    note = 0
    channel = 9
    pattern = [[[Note.OFF] * 16 for _ in range(16)] * 16 for _ in range(16)]
    
    reset_notes()


def update_leds():
    if button_mode == ButtonMode.PATTERN:
        for i in range(16):
            noteType = pattern[channel][note][i]
            if i == step:
                pixels[i] = Color.NOTE if noteType == Note.ON else Color.MARKER
            elif channel == 9:
                pixels[i] = drum_note_colors[note] if noteType == Note.ON else Color.OFF
            else:
                if noteType == Note.ON:
                    pixels[i] = melody_note_colors[note]
                elif noteType == Note.HOLD:
                    pixels[i] = melody_hold_note_colors[note]
                else:
                    pixels[i] = Color.NOTE_OFF
    elif button_mode == ButtonMode.NOTE_CHOOSER:
        for i in range(16):
            if channel == 9:
                if dim_notes[i]:
                    pixels[i] = drum_note_colors[button_map[i]]
                else:
                    pixels[i] = note_dimmed_colors[button_map[i]]
            else:
                pixels[i] = melody_note_colors[button_map[i]]
    elif button_mode == ButtonMode.CHANNEL_CHOOSER:
        for i in range(16):
            pixels[i] = Color.DRUM_CHANNEL if button_map[i] == 9 else Color.CHANNEL
    # don't update if waiting


# midi panic for script reloading
reset_notes()

# main loop
while True:
    lastStep = step
    step = (step + 1) % 16
    update_notes(lastStep, step)
    wait(0.105)
