from kivy.graphics import Fbo, Rectangle, Color
from kivy.graphics.opengl import glFinish
from kivy.uix.widget import Widget
from kivy.app import App
from time import time

def radial_gradient(border_color=(1, 1, 0), center_color=(1, 0, 0), size=(64, 64)):

    fbo = Fbo(size=size)
    fbo.shader.fs = '''
    $HEADER$
    uniform vec3 border_color;
    uniform vec3 center_color;
    void main (void) {
        float d = clamp(distance(tex_coord0, vec2(0.5, 0.5)), 0., 1.);
        gl_FragColor = vec4(mix(center_color, border_color, d), 1);
    }
    '''

    # use the shader on the entire surface
    fbo['border_color'] = map(float, border_color)
    fbo['center_color'] = map(float, center_color)
    with fbo:
        Color(1, 1, 1)
        Rectangle(size=size)
    fbo.draw()

    return fbo.texture

def rectal_gradient(border_color=(1, 1, 0), center_color=(1, 0, 0), size=(64, 64)):

    fbo = Fbo(size=size)
    fbo.shader.fs = '''
    $HEADER$
    uniform vec3 border_color;
    uniform vec3 center_color;
    void main (void) {
        float d = clamp(distance(tex_coord0, vec2(0.5, 0.5)), 0., 1.);
        gl_FragColor = vec4(mix(center_color, border_color, tex_coord0.y), 1);
    }
    '''

    # use the shader on the entire surface
    fbo['border_color'] = map(float, border_color)
    fbo['center_color'] = map(float, center_color)
    with fbo:
        Color(1, 1, 1)
        Rectangle(size=size)
    fbo.draw()

    return fbo.texture


class GpuRadialGradient(App):
    def build(self):
        root = Widget()

        glFinish()
        start = time()
        tex = rectal_gradient()
        glFinish()
        end = time()
        print 'GPU RADIAL BUILD TIME: %.4fms' % ((end - start) * 100)

        with root.canvas:
            Color(1, 1, 1)
            Rectangle(texture=tex, size=(500, 500))
        return root

GpuRadialGradient().run()
