import board
import time
import random

import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange

midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

print("Midi test")

# Convert channel numbers at the presentation layer to the ones musicians use
print("Default output channel:", midi.out_channel + 1)

import adafruit_dotstar
from digitalio import DigitalInOut, Direction, Pull
cs = DigitalInOut(board.GP17)
cs.direction = Direction.OUTPUT
cs.value = 0
pixels = adafruit_dotstar.DotStar(board.GP18, board.GP19, 16, brightness=0.5, auto_write=True)

import busio
from adafruit_bus_device.i2c_device import I2CDevice
i2c = busio.I2C(board.GP5, board.GP4)
device = I2CDevice(i2c, 0x20)

def read_button_states(x, y):
    pressed = [0] * 16
    with device:
        device.write(bytes([0x0]))
        result = bytearray(2)
        device.readinto(result)
        b = result[0] | result[1] << 8
        for i in range(x, y):
            if not (1 << i) & b:
                pressed[i] = 1
            else:
                pressed[i] = 0
    return pressed

last_pressed = [0] * 16

def wait(delay):
    global last_pressed
    s = time.monotonic()
    while time.monotonic() < s + delay:
        pressed = read_button_states(0, 16)
        for i in range(16):
            if pressed[i] and not last_pressed[i]:
                note1[i] = not note1[i]
                pixels[i] = rgb_armed if note1[i] else rgb_off
        last_pressed = pressed
        time.sleep(0.001)


step = 0
rgb_off = (0, 0, 0)
rgb_marker = (16, 16, 16)
rgb_armed = (64, 64, 64)
rgb_note = (255, 255, 255)
note1 = [False] * 16

while True:
    pixels[step] = rgb_armed if note1[step] else rgb_off
    step = (step + 1) % 16
    if note1[step]:
        pixels[step] = rgb_note
        midi.send(NoteOn("C2", 120))
    else:
        pixels[step] = rgb_marker
        midi.send(NoteOff("C2", 120))
    wait(0.125)