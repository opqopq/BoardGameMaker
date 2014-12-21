__author__ = 'HO.OPOYEN'

'''
This example demonstrates creating and usind an AdvancedEffectBase. In
this case, we use it to efficiently pass the touch coordinates into the shader.
'''

from kivy.base import runTouchApp
from kivy.properties import ListProperty
from kivy.lang import Builder
from kivy.uix.effectwidget import EffectWidget, AdvancedEffectBase


effect_string = '''
uniform vec2 touch;

vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
    vec2 distance = 0.025*(coords - touch);
    float dist_mag = (distance.x*distance.x + distance.y*distance.y);
    vec3 multiplier = vec3(abs(sin(dist_mag - time)));
    return vec4(multiplier * color.xyz, 0.5);
}
'''


effect_string_border = '''

uniform vec4 border_color;
uniform int width;

vec4 effect(vec4 vcolor, sampler2D texture, vec2 texcoord, vec2 pixel_coords)
{
    if ((texcoord.x<width/resolution.x) || (texcoord.y<width/resolution.y)) {
        return border_color;
    }
    if ((texcoord.x>(resolution.x-width)/resolution.x) || (texcoord.y>(resolution.y-width)/resolution.y)){
        return border_color;
    }
    return vcolor;
}
'''

effect_string_vflip = '''

vec4 effect(vec4 vcolor, sampler2D texture, vec2 texcoord, vec2 pixel_coords)
{
    return texture2D(texture, vec2(texcoord.x, 1.0-texcoord.y));
}
'''

effect_string_hflip= '''

vec4 effect(vec4 vcolor, sampler2D texture, vec2 texcoord, vec2 pixel_coords)
{
    return texture2D(texture, vec2(1.0-texcoord.x, texcoord.y));
}
'''

from kivy.properties import NumericProperty
class TouchEffect(AdvancedEffectBase):
    touch = ListProperty([0.0, 0.0])
    width = NumericProperty(50)

    def __init__(self, estring, *args, **kwargs):
        super(TouchEffect, self).__init__(*args, **kwargs)
        self.glsl = estring

        self.uniforms = {
                'width': 10,
                'border_color': [.0,1,.0,.0]
        }

    def on_touch(self, *args, **kwargs):
        return
        self.uniforms['touch'] = [float(i) for i in self.touch]


class TouchWidget(EffectWidget):
    def __init__(self, *args, **kwargs):
        super(TouchWidget, self).__init__(*args, **kwargs)
        self.effect = TouchEffect(effect_string_hflip)
        self.effects = [self.effect, TouchEffect(effect_string_vflip)]

    def on_touch_down(self, touch):
        super(TouchWidget, self).on_touch_down(touch)
        self.on_touch_move(touch)

    def on_touch_move(self, touch):
        self.effect.touch = touch.pos


root = Builder.load_string('''
TouchWidget:
    Button:
        text: 'Some text!'
    Image:
        source: 'data/logo/kivy-icon-512.png'
        allow_stretch: True
        keep_ratio: False
''')

runTouchApp(root)
