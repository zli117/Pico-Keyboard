import pcbnew
import os

# X_OFFSET = 50
# Y_OFFSET = 80
X_OFFSET = 0
Y_OFFSET = 0
KEY_MM = 19.05
LEFT_PAD = 8.5
RIGHT_PAD = 8.5
BOTTOM_PAD = 34
CORNER_RADIUS = 5

layout = [
    ['RotaryEncoder_Switch', 'SW_`', 'SW_1', 'SW_2', 'SW_3', 'SW_4', 'SW_5', 'SW_6', 'SW_7', 'SW_8', 'SW_9', 'SW_0', 'SW_-', 'SW_+', 'SW_back'],
    ['SW_esc', 'SW_tab', 'SW_q', 'SW_w', 'SW_e', 'SW_r', 'SW_t', 'SW_y', 'SW_u', 'SW_i', 'SW_o', 'SW_p', 'SW_[', 'SW_]', 'SW_\\'],
    ['SW_del', 'SW_caps', 'SW_a', 'SW_s', 'SW_d', 'SW_f', 'SW_g', 'SW_h', 'SW_j', 'SW_k', 'SW_l', 'SW_;', 'SW_\'', 'SW_enter'],
    ['SW_ins', 'SW_shift', 'SW_z', 'SW_x', 'SW_c', 'SW_v', 'SW_b', 'SW_n', 'SW_m', 'SW_,', 'SW_.', 'SW_/', 'SW_r_shift'],
    ['SW_fn1', 'SW_ctrl', 'SW_super', 'SW_alt', 'SW_space', 'SW_fn2', 'SW_left', 'SW_down', 'SW_up', 'SW_right'],
    # ['SW_m_left', 'SW_m_right'],
]

layout_flatten = sum(layout, [])
switch_names = set(layout_flatten)
assert len(switch_names) == len(layout_flatten), (len(switch_names), len(layout_flatten))

special_sizes = {
    'SW_back': 2.0,
    'SW_tab': 1.5,
    'SW_\\': 1.5,
    'SW_caps': 1.75,
    'SW_enter': 2.25,
    'SW_shift': 2.25,
    'SW_r_shift': 2.75,
    'SW_ctrl': 1.25,
    'SW_super': 1.25,
    'SW_alt': 1.25,
    'SW_space': 6.25,
}

stablizers = {
    'SW_back': 'Stabilizer_Cherry_MX_2.00u',
    'SW_enter': 'Stabilizer_Cherry_MX_2.00u',
    'SW_shift': 'Stabilizer_Cherry_MX_2.00u',
    'SW_r_shift': 'Stabilizer_Cherry_MX_2.00u',
    'SW_space': 'Stabilizer_Cherry_MX_6.25u',
}

STABLIZER_LIB_PATH = 'footprints/com_github_perigoso_keyswitch-kicad-library/Mounting_Keyboard_Stabilizer.pretty'

pcb = pcbnew.GetBoard()

name_to_footprint = dict()
for f in pcb.Footprints():
    show_text = f.Value().GetShownText()
    if show_text in switch_names:
        name_to_footprint[show_text] = f

y = KEY_MM / 2 + Y_OFFSET
name_to_xy = dict()

# Place the switches

for row in layout:
    x = LEFT_PAD + X_OFFSET
    previous_width = 0
    for key in row:
        f = name_to_footprint[key]
        width = special_sizes.get(key, 1.0) * KEY_MM
        x += (previous_width + width) / 2
        f.SetPosition(pcbnew.wxPointMM(x, y))
        #f.Rotate(pcbnew.wxPointMM(x, y), 1800)
        name_to_xy[key] = (x, y)
        previous_width = width
        if key in stablizers:
            stab_name = stablizers[key]
            stab_f = pcbnew.FootprintLoad(os.path.join(os.getenv('KICAD6_3RD_PARTY'), STABLIZER_LIB_PATH),
                                          stab_name)
            stab_f.SetPosition(pcbnew.wxPointMM(x, y))
            stab_f.Reference().SetVisible(False)
            pcb.Add(stab_f)
            #stab_f.Rotate(pcbnew.wxPointMM(x, y), 1800)
    y += KEY_MM

rotary_encoder = pcb.FindFootprintByReference('SW1')
x = name_to_xy['SW_esc'][0] - 7.48
y = name_to_xy['SW_back'][1] - 2.48
#rotary_encoder.Rotate(rotary_encoder.GetPosition(), 1800)
rotary_encoder.SetPosition(pcbnew.wxPointMM(x, y))

joy_stick = pcb.FindFootprintByReference('U1')
x, y = name_to_xy['SW_space']
y += 26
joy_stick.SetPosition(pcbnew.wxPointMM(x, y))
# name_to_footprint['SW_m_left'].SetPosition(pcbnew.wxPointMM(x - 25, y))
# name_to_xy['SW_m_left'] = (x - 25, y)
# name_to_footprint['SW_m_right'].SetPosition(pcbnew.wxPointMM(x + 25, y))
# name_to_xy['SW_m_right'] = (x + 25, y)

# Place the diodes

def flip_text(footprint):
    footprint.Reference().Flip(footprint.Reference().GetPosition(), True)
    drawings = footprint.GraphicalItems()
    for drawing in drawings:
        if isinstance(drawing, pcbnew.FP_TEXT):
            drawing.Flip(drawing.GetPosition(), True)
        else:
            layer_name = drawing.GetLayerName()
            if layer_name[0] == 'F':
                new_layer_name = 'B' + layer_name[1:]
            elif layer_name[0] == 'B':
                new_layer_name = 'F' + layer_name[1:]
            else:
                assert False, layer_name
            drawing.SetLayer(pcb.GetLayerID(new_layer_name))

for key, (x, y) in name_to_xy.items():
    ref_name = name_to_footprint[key].Reference().GetShownText()
    ref_number = int(ref_name[2:]) + 1
    diode_ref = 'D%d' % (ref_number)
    diode = pcb.FindFootprintByReference(diode_ref)
    diode.SetLayer(pcb.GetLayerID('B.Cu'))
    flip_text(diode)
    assert diode, (diode_ref, key)
    diode_position = (x - KEY_MM / 2, y + 5.08)
    diode.SetPosition(pcbnew.wxPointMM(*diode_position))
    diode.Rotate(pcbnew.wxPointMM(*diode_position), 900)

# Place Pico

pico = pcb.FindFootprintByReference('U2')
pico.Flip(pico.GetPosition(), True)
pico.Rotate(pico.GetPosition(), 900)
y = name_to_xy['SW_space'][1] + 14 + KEY_MM / 2
pico.SetPosition(pcbnew.wxPointMM(X_OFFSET + 26, y))  # Length of pico is 52

# Place the screen

x, y = pico.GetPosition()
x = pcbnew.ToMM(x)
y = pcbnew.ToMM(y)
screen = pcb.FindFootprintByReference('J1')
screen.SetPosition(pcbnew.wxPointMM(x + 50, y + 2))

# Add edge cut border lines

switch_width = name_to_xy['SW_right'][0] + KEY_MM / 2
switch_bottom = name_to_xy['SW_space'][1] + KEY_MM / 2

left = pcbnew.PCB_SHAPE()
left.SetStart(pcbnew.wxPointMM(X_OFFSET, Y_OFFSET + CORNER_RADIUS))
left.SetEnd(pcbnew.wxPointMM(X_OFFSET, switch_bottom + BOTTOM_PAD - CORNER_RADIUS))
left.SetLayer(pcb.GetLayerID('Edge.Cuts'))
pcb.Drawings().append(left)

right = pcbnew.PCB_SHAPE()
right.SetStart(pcbnew.wxPointMM(switch_width + RIGHT_PAD, Y_OFFSET + CORNER_RADIUS))
right.SetEnd(pcbnew.wxPointMM(switch_width + RIGHT_PAD, switch_bottom + BOTTOM_PAD - CORNER_RADIUS))
right.SetLayer(pcb.GetLayerID('Edge.Cuts'))
pcb.Drawings().append(right)

top = pcbnew.PCB_SHAPE()
top.SetStart(pcbnew.wxPointMM(X_OFFSET + CORNER_RADIUS, Y_OFFSET))
top.SetEnd(pcbnew.wxPointMM(switch_width + RIGHT_PAD - CORNER_RADIUS, Y_OFFSET))
top.SetLayer(pcb.GetLayerID('Edge.Cuts'))
pcb.Drawings().append(top)

bottom = pcbnew.PCB_SHAPE()
bottom.SetStart(pcbnew.wxPointMM(X_OFFSET + CORNER_RADIUS, switch_bottom + BOTTOM_PAD))
bottom.SetEnd(pcbnew.wxPointMM(switch_width + RIGHT_PAD - CORNER_RADIUS, switch_bottom + BOTTOM_PAD))
bottom.SetLayer(pcb.GetLayerID('Edge.Cuts'))
pcb.Drawings().append(bottom)

# Add corner arcs

top_left = pcbnew.PCB_SHAPE()
top_left.SetShape(pcbnew.SHAPE_T_ARC)
top_left.SetStart(pcbnew.wxPointMM(X_OFFSET, Y_OFFSET + CORNER_RADIUS))
top_left.SetCenter(pcbnew.wxPointMM(X_OFFSET + CORNER_RADIUS, Y_OFFSET + CORNER_RADIUS))
top_left.SetArcAngleAndEnd(900)
top_left.SetLayer(pcb.GetLayerID('Edge.Cuts'))
pcb.Drawings().append(top_left)

top_right = pcbnew.PCB_SHAPE()
top_right.SetShape(pcbnew.SHAPE_T_ARC)
top_right.SetStart(pcbnew.wxPointMM(switch_width + RIGHT_PAD - CORNER_RADIUS, Y_OFFSET))
top_right.SetCenter(pcbnew.wxPointMM(switch_width + RIGHT_PAD - CORNER_RADIUS, Y_OFFSET + CORNER_RADIUS))
top_right.SetArcAngleAndEnd(900)
top_right.SetLayer(pcb.GetLayerID('Edge.Cuts'))
pcb.Drawings().append(top_right)

bottom_right = pcbnew.PCB_SHAPE()
bottom_right.SetShape(pcbnew.SHAPE_T_ARC)
bottom_right.SetStart(pcbnew.wxPointMM(switch_width + RIGHT_PAD, switch_bottom + BOTTOM_PAD - CORNER_RADIUS))
bottom_right.SetCenter(pcbnew.wxPointMM(switch_width + RIGHT_PAD - CORNER_RADIUS, switch_bottom + BOTTOM_PAD - CORNER_RADIUS))
bottom_right.SetArcAngleAndEnd(900)
bottom_right.SetLayer(pcb.GetLayerID('Edge.Cuts'))
pcb.Drawings().append(bottom_right)

bottom_left = pcbnew.PCB_SHAPE()
bottom_left.SetShape(pcbnew.SHAPE_T_ARC)
bottom_left.SetStart(pcbnew.wxPointMM(X_OFFSET + CORNER_RADIUS, switch_bottom + BOTTOM_PAD))
bottom_left.SetCenter(pcbnew.wxPointMM(X_OFFSET + CORNER_RADIUS, switch_bottom + BOTTOM_PAD - CORNER_RADIUS))
bottom_left.SetArcAngleAndEnd(900)
bottom_left.SetLayer(pcb.GetLayerID('Edge.Cuts'))
pcb.Drawings().append(bottom_left)

# Add mounting holes

MOUNTING_HOLE_PATH = os.path.join(os.getenv('KICAD6_FOOTPRINT_DIR'), 'MountingHole.pretty')

centers = [(X_OFFSET + CORNER_RADIUS, Y_OFFSET + CORNER_RADIUS),
           (switch_width + RIGHT_PAD - CORNER_RADIUS, Y_OFFSET + CORNER_RADIUS),
           (switch_width + RIGHT_PAD - CORNER_RADIUS, switch_bottom + BOTTOM_PAD - CORNER_RADIUS),
           (X_OFFSET + CORNER_RADIUS, switch_bottom + BOTTOM_PAD - CORNER_RADIUS)]

for center in centers:
    hole = pcbnew.FootprintLoad(MOUNTING_HOLE_PATH, 'MountingHole_3.2mm_M3_ISO7380_Pad')
    hole.SetPosition(pcbnew.wxPointMM(*center))
    hole.Reference().SetVisible(False)
    pcb.Add(hole)

pcbnew.Refresh()