from kivy.uix.button import Button
from kivy.graphics import Translate, Rectangle,Fbo, ClearColor, ClearBuffers, Rotate, PushMatrix, PopMatrix, Color
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.app import App
from kivy.uix.widget import Widget


def identity(texture):
    return texture

def m_flip(texture):
    texture.flip_horizontal()
    texture.flip_vertical()
    return texture

def gscale(texture):
    from kivy.core.image import Image
    img = Image(texture)
    pixels = img._texture.pixels
    print type(pixels), len(pixels), set(pixels)
    return texture

