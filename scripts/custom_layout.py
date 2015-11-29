hexagon_width = 6.03 # cm
hexagon_height = 6.77 #cm
h_step = 5.94 # step between 2 hex. With my image, it was less than hex_width
v_step = 5.04 # same as above

from conf import card_format, ENV
from utils import alert

main = ENV['main']

if 'layout' not in main.ids:
    main.on_screen_name(main,'layout')

layout = main.ids.layout
stack = layout.ids.pictures

def hexa_layout():
    card_format.size = (hexagon_width, hexagon_height)
    layout.custom_layout(h_step, v_step, 0, "%s/2*(row%%2)"%h_step, "", clean_book_first=True)
    layout.export_phs()
    alert('Layout is done ! ')

def triangle_layout(h,v):
    layout.custom_layout(h,v,180,clean_book_first=True)
    layout.export_phs()
    alert('Layout done')

