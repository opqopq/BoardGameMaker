from kivy.graphics.texture import Texture
from kivy.graphics import Rectangle, Color
from kivy.uix.widget import Widget
from kivy.graphics.opengl import glFinish
from kivy.app import App
from time import time


class RadialGradient(App):
    def build(self):
        root = Widget()

        glFinish()
        start = time()
        tex = self.create_tex()
        glFinish()
        end = time()
        print 'CPU RADIAL BUILD TIME: %.4fms' % ((end - start) * 100)

        with root.canvas:
            Color(1, 1, 1)
            Rectangle(texture=tex, size=(500, 500))

        return root

    def create_tex(self, *args):
        center_color = 255, 255, 0
        border_color = 100, 0, 0

        size = (64, 64)
        tex = Texture.create(size=size)

        sx_2 = size[0] / 2
        sy_2 = size[1] / 2

        buf = ''
        for x in xrange(-sx_2, sx_2):
            for y in xrange(-sy_2, sy_2):
                a = x / (1.0 * sx_2)
                b = y / (1.0 * sy_2)
                d = (a ** 2 + b ** 2) ** .5

                for c in (0, 1, 2):
                    buf += chr(max(0,
                                   min(255,
                                       int(center_color[c] * (1 - d)) +
                                       int(border_color[c] * d))))

        tex.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        return tex

RadialGradient().run()
