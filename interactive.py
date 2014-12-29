__author__ = 'opq'

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse
from kivy.uix.button import Button

from kivy.logger import Logger
Logger.setLevel('WARN')

from kivy.properties import ObjectProperty, ListProperty, DictProperty, StringProperty
from collections import OrderedDict


from kivy.graphics.texture import Texture
from PIL import Image as PILImage
from img_xfos import img_modes

from kivy.lang import Builder
kv = '''
<rootButton@Button>:
    size_hint: None, None
    on_press: print self.text
    text: 'root'
    size: 100,30

<subButton@rootButton>:
    text: "sub"
    on_press: print 'forced sub'

<RootWidget@FloatLayout>:
    Label:
        text: "label"
    rootButton:
        pos: 0,0
        text: 'LB'
    rootButton:
        pos: 100,0
        text: 'RB'
    subButton:
        pos: 0,50
        text: 'TL'
    subButton:
        pos: 100,50
        text: 'TR'


'''

Builder.load_string(kv)
from kivy.uix.floatlayout import FloatLayout

class RootWidget(FloatLayout):
    pass

class TestApp(App):
    def build(self):
        return RootWidget()


TestApp().run()

