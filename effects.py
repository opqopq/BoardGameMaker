"""Contains several class & function for generating texture manipulation thourhg shaders

You'll find:
 - effect_string for Effect class, applying to the EffectField
 - pure Texture provider, to use with SourceShapeField subclass

"""

__author__ = 'HO.OPOYEN'

#################################################################
#                  EffectField Effect                           #
#################################################################

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

effect_circle_grid = """
uniform float radius;
uniform float spacing;
uniform int invert;
vec4 effect(vec4 vcolor, sampler2D texture, vec2 texcoord, vec2 pixel_coords)
{
        vec2 pos = mod(pixel_coords.xy, vec2(50.0)) - vec2(25.0);
        float dist_squared = dot(pos, pos);
        float alpha = (dist_squared < 400.0)
            ? 1.0
            : 0.0;
        if (invert==1) { alpha = 1.0 - alpha;}
        return vec4(vcolor.xyz, alpha);
}
"""

effect_rect_grid = """
uniform float height;
uniform float width;
uniform int line_width;
uniform vec4 line_color;
vec4 effect(vec4 vcolor, sampler2D texture, vec2 texcoord, vec2 pixel_coords)
{
        float x_grid = abs(mod(pixel_coords.x, width));
        float y_grid = abs(mod(pixel_coords.y, height));
        return (x_grid <=line_width) || (y_grid <=line_width)
            ? line_color
            : vec4(0,0,0,0);
        //float alpha = (x_grid <=line_width) || (y_grid <=line_width)
        //    ? 1.0
        //    : 0;
        //return vec4(vcolor.xyz, alpha);
}

"""


moving_target_fs= '''

vec4 effect(vec4 vcolor, sampler2D texture, vec2 texcoord, vec2 pixel_coords)
{
    vec2 position = ( pixel_coords.xy / min(resolution.x, resolution.y) ) - vec2(0.5);
    float distance = sqrt(position.x * position.x + position.y * position.y);

    float fade = (sin(distance * 20.0 - time * 5.0) + 0.5) * 0.5;
    fade = smoothstep(0.0, 0.5, fade);

    return vec4(fade * 0.4, 0.0, fade, 1);
}
'''

grid_fs='''

const float pi = 3.141592653589793;
vec4 effect(vec4 vcolor, sampler2D texture, vec2 texcoord, vec2 pixel_coords)
{

    vec2 p = pixel_coords.xy / resolution;
    p = 2.0 * p - 1.0;
    p.x *= resolution.x / resolution.y;
    vec2 q = abs(p);
    float d = max(q.x + q.y * tan(pi / 6.0), 2.0 * tan(pi / 6.0) * q.y);
    vec3 col = vec3(d - 0.5);
    col = smoothstep(0.01, 0.0, col);
    return vec4(vec3(col), .5);

}
'''

hex_grid_fs='''

const float PI = 3.141592;


vec4 effect(vec4 vcolor, sampler2D texture, vec2 texcoord, vec2 pixel_coords)
{

    vec2 p = ( pixel_coords.xy / resolution.xy );
    p.x = fract(p.x*6.0); //Num hex by row
    p.y = fract(p.y*6.0); // num hex by coloumn
    //p = fract(p*3.0); //num hex by side
    p = p*2.0 - 1.0;
    p.x *= resolution.x/resolution.y;
    vec2 q = abs(p);
    float d = max(q.x + q.y*0.5773, q.y*0.5773*2.0) - 0.1;  // 0.5773 = tan(PI/sqrt(3.0))

	//d = max(q.x + q.y*0.8, q.y*1.15464) -0.1;

    d = smoothstep(0.99, 1.0, d);
    //d = 1.0 - d;
    vec3 col = vec3(d);
    return vec4( col, 0.7 );
}

'''

light_ball_fs='''

float sdf(vec3 p)
{
	return distance(p, vec3(0.0, 0.0, 0.0)) - 1.0;
}

vec3 grad(vec3 p)
{
	const float offs = 0.0001;
	vec3 f = vec3(sdf(p));
	vec3 g = vec3(sdf(p + vec3(offs, 0.0, 0.0)),
		      sdf(p + vec3(0.0, offs, 0.0)),
		      sdf(p + vec3(0.0, 0.0, offs)));
	return (g - f) / offs;
}

vec4 effect(vec4 vcolor, sampler2D texture, vec2 texcoord, vec2 pixel_coords)
{
    vec4 result;

    float ar = resolution.x / resolution.y;
    vec2 p = pixel_coords.xy / resolution;
    p = p * 2.0 - 1.0;
    p.x *= ar;

    vec3 rayOrigin = vec3(0.0, 0.0, 2.0);
    vec3 rayDir = normalize(vec3(p.x, p.y, -radians(90.0)));
    vec3 rayPos = rayOrigin;
    vec3 lightDir = normalize(vec3(0.5, 0.7, 1.0));

    float sd;

    for (int i=0; i<64; i++)
    {
        sd = sdf(rayPos);

        if (abs(sd) < 0.0001)
        {
            vec3 normal = normalize(grad(rayPos));
            float intensity = dot(normal, lightDir);
            result = vec4(vec3(intensity), 0.5);
            return result;
        }

        rayPos = rayPos + rayDir * sd;
    }

    result = vec4(0.0);

    return result;



}
'''

hex_grid_fs2="""
//scale is radius of the hex
#define Scale 150.0
//move is initial padding
#define Move vec2(0.0, 50.0)

uniform vec4 bg_color;
uniform vec4 fg_color;

float hex( vec2 p, vec2 h )
{
    vec2 q = abs(p);
    return max(q.x-h.y,max(q.x+q.y*0.57735,q.y*1.1547)-h.x);
}

vec4 effect(vec4 vcolor, sampler2D texture, vec2 texcoord, vec2 pixel_coords)
{

    vec2 grid = vec2(0.692, 0.4) * Scale;
    float radius = 0.215 * Scale;
    //radius *= pow(min(1.0, max(0.0, pixel_coords.y-0.0)/200.0), 0.8);
    vec2 p = pixel_coords.xy + (Move);

    vec2 p1 = mod(p, grid) - grid*vec2(0.5);
    vec2 p2 = mod(p+grid*0.5, grid) - grid*vec2(0.5);
    float d1 = hex(p1, vec2(radius));
    float d2 = hex(p2, vec2(radius));
    float d = min(d1, d2);
    float c = d>0.0 ? 0.0 : 0.9;

    //g is used a a veil that movesd in time
    //float g = max((mod(pixel_coords.x+pixel_coords.y, 500.0)/200.0), 0.0);

    return  bg_color*vec4(c) + fg_color*vec4(1.0-c);


}


"""
#################################################################
#                  Gradient                                     #
#################################################################

from kivy.uix.effectwidget import AdvancedEffectBase
from kivy.properties import NumericProperty, ListProperty, StringProperty, DictProperty

class Effect(AdvancedEffectBase):
    glsl = StringProperty()
    touch = ListProperty([0.0, 0.0])
    uniforms = DictProperty()

    def __call__(self, **kwargs):
        self.uniforms.update(kwargs)
        return self


def register(name, glsl, force = False):
    if name in effects and not force:
        raise ValueError('Name %s already exists for effects!'%name)
    effects[name] = Effect(glsl=glsl)

def unregister(name):
    del effects[name]

effects = {
    'hflip': Effect(glsl=effect_string_hflip),
    'vflip': Effect(glsl=effect_string_vflip),
    "circle_grid": Effect(glsl = effect_circle_grid, uniforms={'invert': 0, 'radius':20}),
    "grid": Effect(glsl = effect_rect_grid, uniforms={'line_color': (0, 1, 1, 1), 'line_width': 4, 'width':100, 'height':100}),
    "moving_target": Effect(glsl=moving_target_fs),
    "hexgrid": Effect(glsl = hex_grid_fs, uniforms={'radius': .95}),
    "lightball": Effect(glsl = light_ball_fs),
    "hexgrid2": Effect(glsl= hex_grid_fs2, uniforms={'bg_color': (0.0, 0.0, 0.0, 1.0), 'fg_color':(1.0, 1.0, 1.0, 1.0)}),
}


from kivy.graphics import Fbo, Rectangle, Color

radial_grd_fs='''
    $HEADER$
    uniform vec3 border_color;
    uniform vec3 center_color;
    void main (void) {
        float d = clamp(distance(tex_coord0, vec2(0.5, 0.5)), 0., 1.);
        gl_FragColor = vec4(mix(center_color, border_color, d), 1);
    }
    '''

h_rect_grd_fs='''
    $HEADER$
    uniform vec3 border_color;
    uniform vec3 center_color;
    void main (void) {
        float d = clamp(distance(tex_coord0, vec2(0.5, 0.5)), 0., 1.);
        gl_FragColor = vec4(mix(center_color, border_color, tex_coord0.y), 1);
    }
    '''

v_rect_grd_fs='''
    $HEADER$
    uniform vec3 border_color;
    uniform vec3 center_color;
    void main (void) {
        float d = clamp(distance(tex_coord0, vec2(0.5, 0.5)), 0., 1.);
        gl_FragColor = vec4(mix(center_color, border_color, tex_coord0.x), 1);
    }
    '''



def advanced_gradient(border_color=(1, 1, 0), center_color=(1, 0, 0), size=(64, 64),fs=radial_grd_fs):

    fbo = Fbo(size=size)
    fbo.shader.fs = fs

    # use the shader on the entire surface
    fbo['border_color'] = map(float, border_color)
    fbo['center_color'] = map(float, center_color)
    with fbo:
        Color(1, 1, 1)
        Rectangle(size=size)
    fbo.draw()

    return fbo.texture

from functools import partial
radial_gradient = partial(advanced_gradient, fs=radial_grd_fs)
h_gradient = partial(advanced_gradient, fs=h_rect_grd_fs)
v_gradient = partial(advanced_gradient, fs=v_rect_grd_fs)




#################################################################
#                     Experiement                               #
#################################################################

circle_test = """
    $HEADER$
    void main (void) {

        vec2 pos = mod(gl_FragCoord.xy, vec2(50.0)) - vec2(25.0);
        float dist_squared = dot(pos, pos);
        gl_FragColor = (dist_squared < 400.0)
            ? vec4(.90, .90, .90, 1.0)
            : vec4(.20, .20, .40, 1.0);
    }
 """

def circle_fs(size=(64, 64)):

    fbo = Fbo(size=size)
    fbo.shader.fs = circle_test

    with fbo:
        Color(1, 1, 1)
        Rectangle(size=size)
    fbo.draw()
    return fbo.texture


#################################################################
#                  Color Effect                                 #
#################################################################

hue_xfo="""
$HEADER$
const mat3 rgb2yiq = mat3(0.299, 0.587, 0.114, 0.595716, -0.274453, -0.321263, 0.211456, -0.522591, 0.311135);
const mat3 yiq2rgb = mat3(1.0, 0.9563, 0.6210, 1.0, -0.2721, -0.6474, 1.0, -1.1070, 1.7046);
uniform float hue;

void main() {

    vec3 yColor = rgb2yiq * texture2DRect(texture0, gl_TexCoord[0].st).rgb;

    float originalHue = atan(yColor.b, yColor.g);
    float finalHue = originalHue + hue;

    float chroma = sqrt(yColor.b*yColor.b+yColor.g*yColor.g);

    vec3 yFinalColor = vec3(yColor.r, chroma * cos(finalHue), chroma * sin(finalHue));
    gl_FragColor    = vec4(yiq2rgb*yFinalColor, 1.0);
}
"""

hue_xfo='''
$HEADER$
uniform float   hueAdjust;
void main ()
{
    const vec4  kRGBToYPrime = vec4 (0.299, 0.587, 0.114, 0.0);
    const vec4  kRGBToI     = vec4 (0.596, -0.275, -0.321, 0.0);
    const vec4  kRGBToQ     = vec4 (0.212, -0.523, 0.311, 0.0);

    const vec4  kYIQToR   = vec4 (1.0, 0.956, 0.621, 0.0);
    const vec4  kYIQToG   = vec4 (1.0, -0.272, -0.647, 0.0);
    const vec4  kYIQToB   = vec4 (1.0, -1.107, 1.704, 0.0);

    // Sample the input pixel
    vec4    color   = texture2DRect (inputTexture, gl_TexCoord [ 0 ].xy);

    // Convert to YIQ
    float   YPrime  = dot (color, kRGBToYPrime);
    float   I      = dot (color, kRGBToI);
    float   Q      = dot (color, kRGBToQ);

    // Calculate the hue and chroma
    float   hue     = atan (Q, I);
    float   chroma  = sqrt (I * I + Q * Q);

    // Make the user's adjustments
    hue += hueAdjust;

    // Convert back to YIQ
    Q = chroma * sin (hue);
    I = chroma * cos (hue);

    // Convert back to RGB
    vec4    yIQ   = vec4 (YPrime, I, Q, 0.0);
    color.r = dot (yIQ, kYIQToR);
    color.g = dot (yIQ, kYIQToG);
    color.b = dot (yIQ, kYIQToB);

    // Save the result
    gl_FragColor    = color;
}
'''


hue_xfo2='''
$HEADER$
precision mediump float;
varying vec2 vTextureCoord;
varying vec3 vHSV;
uniform sampler2D sTexture;



vec3 rgb2hsv(vec3 c)
{
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c)
{
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main() {
    vec4 textureColor = texture2D(sTexture, vTextureCoord);
    vec3 fragRGB = textureColor.rgb;
    vec3 fragHSV = rgb2hsv(fragRGB).xyz;
    fragHSV.x += vHSV.x / 360.0;
    fragHSV.yz *= vHSV.yz;
    fragHSV.xyz = mod(fragHSV.xyz, 1.0);
    fragRGB = hsv2rgb(fragHSV);
    gl_FragColor = vec4(fragRGB, textureColor.w);
}
'''


def hue_transform(source, hue, size=(64, 64)):

    fbo = Fbo(size=size)
    fbo.shader.fs = hue_xfo

    # use the shader on the entire surface
    fbo['hueAdjust'] = float(hue)

    with fbo:
        Color(1, 1, 1)
        Rectangle(size=size, source=source)
    fbo.draw()

    return fbo.texture

maskeffect='''
vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
    return vec4(1.0 - color.xyz, 1.0);
}
'''

class MaskEffect(AdvancedEffectBase):
    def __init__(self, *args, **kwargs):
        super(MaskEffect, self).__init__(*args, **kwargs)
        self.glsl = maskeffect
        self.uniforms = {'touch':[0.0, 0.0]}

    def on_touch(self, *args, **kwargs):
        self.uniforms['touch']= [float(i) for i in self.touch]

from kivy.uix.effectwidget import EffectWidget

class MaskWidget(EffectWidget):
    def __init__(self, *args, **kwargs):
        super(MaskWidget, self).__init__(*args, **kwargs)
        self.effect = MaskEffect()
        self.effects = [self.effect]
