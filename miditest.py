import board
import time
import random
import usb_midi
import adafruit_midi
from adafruit_midi.control_change import ControlChange
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from adafruit_midi.pitch_bend import PitchBend

import adafruit_dotstar

midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

print("Midi test")

# Convert channel numbers at the presentation layer to the ones musicians use
print("Default output channel:", midi.out_channel + 1)

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

def wait(delay):
    s = time.monotonic()
    while time.monotonic() < s + delay:
        pressed = read_button_states(0, 16)
        if pressed[0]:
            pixels[0] = (255, 255, 255)
        else:
            pixels[0] = (0, 0, 0)
        time.sleep(0.001)

while True:
    pixels[15] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    # midi.send(NoteOn("C4", 120))  # G sharp 2nd octave
    wait(0.25)
    # a_pitch_bend = PitchBend(random.randint(0, 16383))
    # midi.send(a_pitch_bend)
    # note how a list of messages can be used
    pixels[15] = (0, 0, 0)
    midi.send([NoteOff("C4", 120), ControlChange(3, 44)])
    wait(0.5)
