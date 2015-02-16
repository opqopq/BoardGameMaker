__author__ = 'HO.OPOYEN'

from kivy.logger import Logger
Logger.setLevel('DEBUG')
from kivy.base import runTouchApp

from fields import ColorField, ImageField, textured, Textured
from kivy.uix.button import Button
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.interactive import InteractiveLauncher
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout

from kivy.uix.widget import Widget

from kivy.lang import Builder

kv="""

<RootWidget>:
    size: cm(5), cm(8)
    canvas.before:
        StencilPush
        Mesh:
            vertices: self.vertices
            indices: range(len(self.vertices)/4)
            mode: 'triangle_fan'
            #source: self.source
            #texture: self.texture
        StencilUse
    canvas.after:
        #Remove mask
        StencilPop


    points: .25,0.0,  .75,.0, 1.0,.25, 1.0,.75, .75,1.0, .25,1.0, 0.0,.75, 0.0,.25
    #texture: widget.texture
    ColorField:
        id: widget
        source: 'images/red.png'
        text: "erzerzerzerzerzerzerzerze"*100
        size: root.size
        size_hint: None, None
        allow_stretch: True
        keep_ratio: False
        rgba: 1,1 ,0,.5
"""

Builder.load_string(kv)

class RootWidget(FloatLayout):
    vertices = ListProperty()
    points = ListProperty()

    def on_points(self, instance, points):
        from math import cos, sin, pi, radians
        cx, cy = self.pos
        self.vertices = []
        for i in range(0,len(points), 2):
            self.vertices.append(cx + points[i] * self.width)
            self.vertices.append(cy+points[i+1] * self.height)
            #Texture have to be vertically flipped for kivy to load. why ???
            self.vertices.extend([points[i], 1-points[i+1]])

    def add_widget(self, *largs):
        largs= list (largs)
        from kivy.graphics.texture import Texture
        if not hasattr(largs[0],'texture'):
            print 'not texture -> wrapping', largs[0],
            largs[0] = textured(largs[0])
        # trick to attach graphics instructino to fbo instead of canvas
        ret = super(RootWidget, self).add_widget(*largs)
        self.texture = largs[0].texture
        self.on_points(self, self.points)
        return ret


class MyApp(App):
    def build(self):
        return RootWidget()
# needed to create Fbo, must be resolved in future kivy version
from kivy.core.window import Window

from kivy.graphics import Color, Rectangle, Canvas
from kivy.graphics.fbo import Fbo
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty


MyApp().run()