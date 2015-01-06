__author__ = 'opq'



from kivy.uix.floatlayout import FloatLayout
from kivy.graphics.opengl import glBlendFunc, glBlendFuncSeparate, glBlendEquationSeparate, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, glBlendEquation, GL_FUNC_ADD, GL_FUNC_SUBTRACT, GL_FUNC_REVERSE_SUBTRACT
from kivy.core.image import Image
from kivy.graphics import Rectangle, Color, Callback, RenderContext, BindTexture
from kivy.factory import Factory
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse
from kivy.uix.button import Button
from kivy.graphics.opengl import glBlendFunc, GL_SRC_ALPHA, GL_ONE, GL_ZERO, GL_SRC_COLOR, GL_ONE_MINUS_SRC_COLOR, GL_ONE_MINUS_SRC_ALPHA, GL_DST_ALPHA, GL_ONE_MINUS_DST_ALPHA, GL_DST_COLOR, GL_ONE_MINUS_DST_COLOR
from kivy.properties import NumericProperty, ObjectProperty

from kivy.logger import Logger
Logger.setLevel('WARN')

from kivy.properties import ObjectProperty, ListProperty, DictProperty, StringProperty
from collections import OrderedDict


from kivy.graphics.texture import Texture
from PIL import Image as PILImage
from img_xfos import img_modes

from kivy.uix.widget import Widget
from kivy.graphics.opengl import glBlendFunc



#####################################################################
# Utils spinner, which handle keyboard touch
####################################################################
from kivy.uix.spinner import Spinner
from kivy.uix.behaviors import FocusBehavior

def find_char(char, names_list):
    for index, elt in enumerate(names_list):
        if elt.startswith(char):
            return index

class KeyboardSpinner(FocusBehavior, Spinner):

    def keyboard_on_key_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'up':
            self.text = self.values[max(0,self.values.index(self.text)-1)]
        elif keycode[1] == 'down':
           self.text = self.values[min(self.values.index(self.text)+1, len(self.values)-1)]
        else:
            self.text = self.values[find_char(keycode[1], self.values) or self.values.index(self.text)]
        return True

Factory.register('KeyboardSpinner', KeyboardSpinner)

##########################################################################
# Blend opptions
#########################################################################

BLENDS ={
    "GL_SRC_ALPHA": GL_SRC_ALPHA,
    "GL_ONE": GL_ONE,
    "GL_ZERO": GL_ZERO,
    "GL_SRC_COLOR": GL_SRC_COLOR,
    "GL_ONE_MINUS_SRC_COLOR": GL_ONE_MINUS_SRC_COLOR,
    'GL_ONE_MINUS_SRC_ALPHA': GL_ONE_MINUS_SRC_ALPHA,
    'GL_DST_ALPHA': GL_DST_ALPHA,
    'GL_ONE_MINUS_DST_ALPHA': GL_ONE_MINUS_DST_ALPHA,
    'GL_DST_COLOR': GL_DST_COLOR,
    'GL_ONE_MINUS_DST_COLOR': GL_ONE_MINUS_DST_COLOR
}

BLENDSA ={
    "GL_SRC_ALPHA": GL_SRC_ALPHA,
    "GL_ONE": GL_ONE,
    "GL_ZERO": GL_ZERO,
    "GL_SRC_COLOR": GL_SRC_COLOR,
#    "GL_ONE_MINUS_SRC_COLOR": GL_ONE_MINUS_SRC_COLOR,
#    'GL_ONE_MINUS_SRC_ALPHA': GL_ONE_MINUS_SRC_ALPHA,
    'GL_DST_ALPHA': GL_DST_ALPHA,
#    'GL_ONE_MINUS_DST_ALPHA': GL_ONE_MINUS_DST_ALPHA,
    'GL_DST_COLOR': GL_DST_COLOR,
#    'GL_ONE_MINUS_DST_COLOR': GL_ONE_MINUS_DST_COLOR
}

EQUATION = {
    'GL_FUNC_ADD': GL_FUNC_ADD,
    'GL_FUNC_REVERSE_SUBTRACT': GL_FUNC_REVERSE_SUBTRACT,
    'GL_FUNC_SUBTRACT': GL_FUNC_SUBTRACT
}


from kivy.lang import Builder

##############################################
# using shape & stencil use
##############################################

from kivy.graphics import StencilPop, StencilPush, StencilUnUse, StencilUse
class MaskShapeField(Widget):
    shapes = ListProperty()
    _glshapes = ListProperty()

    def __init__(self,**kwargs):
        Widget.__init__(self, **kwargs)

        with self.canvas.before:
            StencilPush()
            StencilUse()
        with self.canvas.after:
            StencilUnUse()
            StencilPop()


    def on_shapes(self, instance, shapes):
        self.canvas.before.clear()
        self._glshapes = []
        from kivy.graphics.instructions import VertexInstruction, Instruction
        from fields import Field
        with self.canvas.before:
            StencilPush()
            for shape, args in shapes:
                if not isinstance(shape, Field):
                    res= shape(**args)
                    print 'instruction ok:', res

                else:
                    res= shape(**args)
                    print 'not an instrcution. taking canvas', res
                    self.canvas.before.add(res.canvas)
                self._glshapes.append(res)
            StencilUse()

Factory.register('MaskShapeField', MaskShapeField)

kv = '''

<RootWidget@FloatLayout>:
    canvas.before:
        Color:
            rgb: 0,1,0
        Rectangle:
            size: self.size
    Button:
        pos: 300,300
        text: "test"
        size_hint: None, None
        on_press: app.add_shape()
    MaskShapeField:
        size_hint: None, None
        size: 200,300
        pos: 200,0
        id: mask
        Image:
            source: 'images/red.png'
            size_hint: None, None
            size: 200,300
            pos: 200,0
'''




Builder.load_string(kv)


class TextureTestApp(App):
    def build(self):
        root = Factory.RootWidget()
        return root

    def add_shape(self):
        mask = self.root.ids.mask
        from fields import RectangleField
        from random import choice
        from kivy.graphics import Rectangle
        alls = [
            (RectangleField, {'size':mask.size,'pos':mask.pos}),
            (Rectangle, {'size':mask.size,'pos':mask.pos}),
        ]
        mask.shapes.append(choice(alls))

##############################################
# using texture multiplication
##############################################

SRC = 'images/red.png'
MASK = 'images/mask.png'


fs_multitexture = '''
$HEADER$
// New uniform that will receive texture at index 1
uniform sampler2D texture1;
void main(void) {
    // multiple current color with both texture (0 and 1).
    // currently, both will use exactly the same texture coordinates.
    gl_FragColor = frag_color * \
        texture2D(texture0, tex_coord0) * \
        texture2D(texture1, tex_coord0);
}
'''


class FileMaskImage(Widget):
    target = ObjectProperty()

    def __init__(self, **kwargs):

        from kivy.graphics import Canvas, Translate, Fbo, ClearColor, ClearBuffers, Scale
        self.canvas = RenderContext()
        self.canvas.shader.fs = fs_multitexture
        for k in kwargs:
            setattr(self,k, kwargs[k])

        with self.canvas:
            Color(1, 1, 1)
            self.fbo = Fbo(size=self.size)
            # here, we are binding a custom texture at index 1
            # this will be used as texture1 in shader.
            BindTexture(texture=self.fbo.texture, index=1)

            # create a rectangle with texture (will be at index 0)
            self.rectangle = Rectangle(size=self.size, source=MASK, pos=self.pos)

        # set the texture1 to use texture index 1
        self.canvas['texture1'] = 1

        # call the constructor of parent
        # if they are any graphics object, they will be added on our new canvas
        super(FileMaskImage, self).__init__(**kwargs)

        # We'll update our glsl variables in a clock
        Clock.schedule_interval(self.update_glsl, 0)
        self.bind(pos=self.update_sp, size=self.update_sp)

    def update_sp(self,instance,value):
        self.rectangle.size = self.size
        self.rectangle.pos = self.pos

    def update_glsl(self, *largs):
        # This is needed for the default vertex shader.
        self.canvas['projection_mat'] = Window.render_context['projection_mat']
        self.canvas['modelview_mat'] = Window.render_context['modelview_mat']

    def on_target(self, instance, target):
        if self.target:
            print 'on target,', target
            from kivy.graphics import Canvas, Translate, Fbo, ClearColor, ClearBuffers, Scale

            if self.target.parent is not None:
                canvas_parent_index = self.parent.canvas.indexof(self.canvas)
                self.parent.canvas.remove(self.canvas)

            with self.fbo:
                ClearColor(1,1,1,0)
                ClearBuffers()
                Scale(1, -1, 1)

            #self.fbo.add(self.target.canvas)
            #self.fbo.draw()
            self.fbo.remove(self.target.canvas)
            if self.target.parent is not None:
                self.target.parent.canvas.insert(canvas_parent_index, self.target.canvas)

Factory.register('FileMaskImage',FileMaskImage)

kv ='''
<RootMultWidget@FloatLayout>:
    canvas.before:
        Color:
            rgb: 0,0,0
        Rectangle:
            size: self.size
    Label:
        source: 'images/red.png'
        size_hint: None, None
        pos: 300,100
        text: 'TOTO\\n'*10
        id: IMG
    FileMaskImage:
        size_hint: None, None
        size: 200,100
        pos: 200,0
        target: IMG
'''

Builder.load_string(kv)


class MultTextureTestApp(App):
    def build(self):
        root = Factory.RootMultWidget()
        return root

##############################################
# using glBlencFunc (spinner / grid)
##############################################


kv='''
<Figure@BoxLayout>
    on_touch_down: if self.collide_point(*args[1].pos): self.opacity=0
    size_hint: None, None
    size: 200, 300
    orientation: 'vertical'
    canvas.before:
        Color:
            rgb: .6,.6,.6
        Rectangle:
            size: self.size
            pos: self.pos
    canvas.after:
        Color:
            rgb: 1,1,1
        Line:
            rectangle: self.x, self.y, self.width, self.height
            width: 2

    RelativeLayout:
        size_hint_y: None
        height: root.height - 100
        TextureMaskWidget:
            mask: 'images/mask.png'
            id: mask
            Image:
                source: 'images/red.png'
                text: "AZERTPOIUYTR\\n"*10
                allow_stretch: True
                keep_ratio: False
                size: mask.size
                pos: mask.pos

    Label:
        size_hint_y: None
        height: 20
        id: eq
        font_size: 12
#    Label:
#        size_hint_y: None
#        height: 20
#        id: srca
#        font_size: 12
#    Label:
#        size_hint_y: None
#        height: 20
#        id: dsta
#        font_size: 12
    Label:
        size_hint_y: None
        height: 20
        id: src
        font_size: 12
    Label:
        size_hint_y: None
        height: 20
        id: dst
        font_size: 12

<RootSpinnerWidget@FloatLayout>:
    canvas.before:
        Color:
            rgb: 0,0,1
        Rectangle:
            size: self.size
            pos: self.pos

    TextureMaskWidget:
        size_hint: .5,1
        source: 'images/mask.png'
        id: DST
        Image:
            source: 'images/red.png'
            size_hint: .5,1
            pos: DST.pos
            size: DST.size

    KeyboardSpinner:
        size_hint: None,None
        size: 300,30
        text: 'GL_ONE'
        id: sp_fg
        right: root.right
        top: root.top

    KeyboardSpinner:
        size_hint: None,None
        size: 300,30
        text: 'GL_ONE_MINUS_SRC_ALPHA'
        id: sp_bg
        right: root.right
        top: sp_fg.y-30

    KeyboardSpinner:
        size_hint: None,None
        size: 300,30
        text: 'GL_ONE'
        id: sp_fga
        right: root.right - 300
        top: root.top

    KeyboardSpinner:
        size_hint: None,None
        size: 300,30
        text: 'GL_ONE_MINUS_SRC_ALPHA'
        id: sp_bga
        right: root.right - 300
        top: sp_fg.y-30

    KeyboardSpinner:
        size_hint: None,None
        size: 300,30
        text: 'GL_FUNC_ADD'
        id: sp_eq
        right: root.right
        top: sp_bg.y-30

<RootGridWidget@ScrollView>:
    StackLayout:
        id: stack
        size_hint_y: None
        orientation: 'lr-tb'
        on_minimum_height: self.height=self.minimum_height

'''

from kivy.uix.image import Image as KVImage
class TextureMaskWidget(Widget):
    blend_factor_source = NumericProperty(GL_ONE)
    blend_factor_dest = NumericProperty(GL_ONE_MINUS_SRC_ALPHA)
    blend_factor_alpha_source = NumericProperty(GL_ONE)
    blend_factor_alpha_dest = NumericProperty(GL_ONE_MINUS_SRC_ALPHA)
    reset_blend_factor_source = NumericProperty(GL_SRC_ALPHA)
    reset_blend_factor_dest = NumericProperty(GL_ONE_MINUS_SRC_ALPHA)
    equation = NumericProperty(GL_FUNC_ADD)

    mask = ObjectProperty()
    def __init__(self, **kwargs):
        super(TextureMaskWidget, self).__init__(**kwargs)

        with self.canvas.before:
            self.rectangle = Rectangle(size = self.size, pos = self.pos, source = 'images/mask.png')
            Callback(self._set_blend_func)

        with self.canvas.after:
            Callback(self._reset_blend_func)


    def _set_blend_func(self, instruction):
        #print self.blend_factor_source, self.blend_factor_dest, self.blend_factor_alpha_source, self.blend_factor_alpha_dest
        #glBlendFuncSeparate(self.blend_factor_source, self.blend_factor_dest, self.blend_factor_alpha_source, self.blend_factor_alpha_dest)
        glBlendFunc(self.blend_factor_source, self.blend_factor_dest)
        #glBlendFuncSeparate(GL_ZERO, GL_SRC_COLOR, self.blend_factor_alpha_source, self.blend_factor_alpha_dest)
        #glBlendEquationSeparate(GL_FUNC_ADD, GL_FUNC_REVERSE_SUBTRACT)

    def _reset_blend_func(self, instruction):
        #glBlendFunc(GL_ONE, GL_ZERO)
        #glBlendFuncSeparate(self.reset_blend_factor_source, self.reset_blend_factor_dest,self.reset_blend_factor_source, self.reset_blend_factor_dest)
        #glBlendEquation(GL_FUNC_ADD)
        glBlendFunc(self.reset_blend_factor_source, self.reset_blend_factor_dest)
        #glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE)

    def on_mask(self, instance, mask):
        self.rectangle.source = mask

    def on_pos(self, instance, pos):
        self.rectangle.pos = pos

    def on_size(self, instance, size):
        self.rectangle.size = size

Factory.register('TextureMaskWidget', TextureMaskWidget)

Builder.load_string(kv)


class SpinnerTestApp(App):
    def build(self):
        root = Factory.RootSpinnerWidget()
        DST = root.ids.DST
        spfg = root.ids.sp_fg
        spbg = root.ids.sp_bg
        spfga = root.ids.sp_fga
        spbga = root.ids.sp_bga
        speq = root.ids.sp_eq
        spfg.values = spbg.values = spbga.values = spfga.values =  "GL_SRC_ALPHA, GL_ONE, GL_ZERO, GL_SRC_COLOR, GL_ONE_MINUS_SRC_COLOR, GL_ONE_MINUS_SRC_ALPHA, GL_DST_ALPHA, GL_ONE_MINUS_DST_ALPHA, GL_DST_COLOR, GL_ONE_MINUS_DST_COLOR".split(', ')
        speq.values = EQUATION.keys()
        def update_src_blend(instance, value):
            DST.blend_factor_source = BLENDS[value]
        def update_dst_blend(instance, value):
            DST.blend_factor_dest = BLENDS[value]
        def update_src_alpha_blend(instance, value):
            DST.blend_factor_alpha_source = BLENDS[value]
        def update_dst_alpha_blend(instance, value):
            DST.blend_factor_alpha_dest = BLENDS[value]
        def update_eq(instance, value):
            DST.equation = EQUATION[value]
        spfg.bind(text=update_src_blend)
        spbg.bind(text=update_dst_blend)
        spfga.bind(text=update_src_alpha_blend)
        spbga.bind(text=update_dst_alpha_blend)
        speq.bind(text=update_eq)
        return root

class GridTestApp(App):
    def build(self):
        FIG = Factory.Figure
        root = Factory.RootGridWidget()
        stack = root.ids.stack
        #for asrc in (sorted(BLENDSA)):
        #    for adst in (sorted(BLENDSA)):
        for eq in sorted(EQUATION):
            for src in (sorted(BLENDS)):
                for dst in (sorted(BLENDS)):
                    f = FIG()
                    f.ids.mask.blend_factor_source = BLENDS[src]
                    f.ids.mask.blend_factor_dest = BLENDS[dst]
    #                f.ids.mask.blend_factor_alpha_source = BLENDSA[asrc]
    #                f.ids.mask.blend_factor_alpha_dest = BLENDSA[adst]
                    f.ids.mask.equation = EQUATION[eq]
                    f.ids.src.text = 'SRC: '+src
                    f.ids.dst.text = 'DST: '+dst
    #                f.ids.srca.text= 'ASRC: '+asrc
    #                f.ids.dsta.text= 'ADST: '+adst
                    f.ids.eq.text = 'EQ:' + eq
                    stack.add_widget(f)
        return root


TestApp = TextureTestApp
#TestApp = GridTestApp
#TestApp = SpinnerTestApp
TestApp().run()
