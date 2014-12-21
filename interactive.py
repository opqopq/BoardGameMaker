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
<TransfoField>:

    canvas:
        Rectangle:
            pos: self.pos
            size: self.size
            texture: self.texture
'''

Builder.load_string(kv)
class TransfoField(Widget):
    "Transform an image file thourgh different methods registered in img_xfos.py"
    default_attr = 'source'
    not_exported = ['texture', 'Image']
    texture = ObjectProperty(allownone=True)
    source = StringProperty()
    xfos = ListProperty()
    Image = ObjectProperty()

    def on_source(self, instance, source):
        from os.path import isfile
        self.Image = PILImage.open(source)
        if isfile(source):
            for xfo in self.xfos:
                self.Image = xfo(self.Image)
        self.prepare_texture()

    def on_xfos(self, instance, xfos):
        if self.source:
            self.on_source(instance, self.source)

    def prepare_texture(self):
        self.texture = None
        #Flip it, for kv
        from kivy.core.image import Image as KImage, ImageData
        #Pseicla case for luminace mode
        if self.Image.mode.startswith('L'):
            from kivy.logger import Logger
            Logger.warn('Greyscale picture in XFOField: resorting to disk usage')
            self.Image.save('build/%s.png'%id(self))
            ktext = KImage('build/%s.png'%id(self)).texture
            self.texture = ktext
            return
        #Standard mode: flip the
        flip = self.Image.transpose(PILImage.FLIP_TOP_BOTTOM)
        w, h = flip.size
        imgdata = ImageData(w, h, img_modes[flip.mode], data=flip.tobytes())
        ktext = Texture.create_from_data(imgdata)
        self.texture = ktext

class MyPaintWidget(Widget):

    def __init__(self,**kwargs):
        Widget.__init__(self, **kwargs)
        b = Button(text= "press", size_hint=(None, None))

        xfo = TransfoField()
        self.add_widget(b)
        self.add_widget(xfo)
        self.button = b
        self.xfo = xfo
        xfo.source= 'images/judge.jpg'
        xfo.pos = (200, 200)
        xfo.size_hint = None, None
        from img_xfos import h_flip as gs
        from img_xfos import v_flip as vs
        from img_xfos import grey_opencv as GOCV
        xfo.xfos = [gs, vs, GOCV]



class TestApp(App):
    def build(self):
        return MyPaintWidget()


TestApp().run()

