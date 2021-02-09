import time
import picokeypad as keypad

keypad.init()
keypad.set_brightness(0.75)

NUM_PADS = keypad.get_num_pads()

i = 0
colour_index = 0

while True:
    if colour_index == 0:
        keypad.illuminate(i, 0, 255, 0)
    elif colour_index == 1:
        keypad.illuminate(i, 255, 255, 0x00)
    elif colour_index == 2:
        keypad.illuminate(i, 255, 0x00, 0x00)
    elif colour_index == 3:
        keypad.illuminate(i, 255, 0x00, 255)
    elif colour_index == 4:
        keypad.illuminate(i, 0x00, 0x00, 255)
    elif colour_index == 5:
        keypad.illuminate(i, 0x00, 255, 255)
    keypad.update()
    
    i += 1
    if i > 15:
        i = 0
        colour_index += 1
        if colour_index > 5:
            colour_index = 0
    time.sleep(0.05)
