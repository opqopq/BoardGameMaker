
__all__ = ('start', 'stop')

from kivy.uix.floatlayout import FloatLayout
from kivy.properties import BooleanProperty, ObjectProperty, \
        NumericProperty
from kivy.graphics import Fbo, ClearColor, ClearBuffers, \
        RenderContext, Callback, PushMatrix, PopMatrix, \
        Color, Translate, Rotate, Mesh, UpdateNormalMatrix, \
        Canvas, Line
from kivy.graphics.opengl import glEnable, glDisable, GL_DEPTH_TEST
from kivy.graphics.transformation import Matrix
from kivy.clock import Clock
from kivy.animation import Animation
from random import random
from math import sin, cos, pi
from functools import partial

fs = '''
#ifdef GL_ES
    precision highp float;
#endif

varying vec4 color_vec;
varying vec2 tc0_vec;

uniform sampler2D texture0;

void main (void){
    vec4 t = texture2D(texture0, tc0_vec);
    gl_FragColor = t * color_vec;
}
'''

vs = '''
#ifdef GL_ES
    precision highp float;
#endif

attribute vec3  v_pos;
attribute vec3  v_normal;
attribute vec4  v_color;
attribute vec2  v_tc0;

uniform mat4 modelview_mat;
uniform mat4 projection_mat;

varying vec4 color_vec;
varying vec2 tc0_vec;

void main (void) {
    color_vec = v_color;
    tc0_vec = v_tc0;
    gl_Position = projection_mat * modelview_mat * vec4(v_pos, 1.0);
}
'''

# XXX taken from context_graphics. Should be available in a kivy.graphics.color
# instead.
def hsv_to_rgb(h, s, v):
    if s == 0.0: return v, v, v
    i = int(h * 6.0) # XXX assume int() truncates!
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    if i == 0: return v, t, p
    if i == 1: return q, v, p
    if i == 2: return p, v, t
    if i == 3: return p, q, v
    if i == 4: return t, p, v
    if i == 5: return v, p, q
    # Cannot get here


class Inspector3d(FloatLayout):

    activated = BooleanProperty(False)

    win = ObjectProperty()

    cam_dist = NumericProperty(630)
    cam_theta = NumericProperty(pi / 2.)
    cam_phi = NumericProperty(pi / 2.)
    cam_sensitivity = NumericProperty(2.)
    object_thick = NumericProperty(0.)
    line_alpha = NumericProperty(0.)

    def create_3d(self):
        self.hue_cache = {}
        self.canvas.clear()
        Clock.schedule_interval(self.update_glsl, 1 / 60.)
        win = self.win
        self._children = self.win.children[:]
        self.size = win.size

        # create an fbo container for all the window children
        # this will be used for texturing.
        # add widget into our canvas
        self.fbo = fbo = Fbo(size=win.size)
        with fbo:
            ClearColor(0, 0, 0, 1)
            ClearBuffers()
        canvas = self.canvas
        self.canvas = fbo
        for child in win.children:
            win.remove_widget(child)
            self.add_widget(child)
        self.canvas = canvas

        # now create the 3d representation
        with self.canvas:
            self.rc = rc = RenderContext()
            rc.shader.vs = vs
            rc.shader.fs = fs

        with rc.before:
            Callback(self.setup_gl_context)
            PushMatrix()
            Color(1, 1, 1, 1)
            Translate(-self.width / 2., -self.height / 2., 0)

        with rc.after:
            PopMatrix()
            Callback(self.reset_gl_context)

        with rc:
            self.rc_back = Canvas()
            self.rc_front = Canvas()
            self.rc_line = Canvas()

        # add ourself in the window
        win.add_widget(self)

        self.refresh()

        # show nice entering animation
        self.cam_dist = self.property('cam_dist').defaultvalue
        self.cam_theta = self.property('cam_theta').defaultvalue
        self.cam_phi = self.property('cam_phi').defaultvalue
        self.object_thick = self.property('object_thick').defaultvalue
        (
                Animation(cam_dist=1200, t='in_out_quad') + (\
                Animation(cam_theta=pi / 2. + .5, t='out_quad') & \
                Animation(object_thick=20., line_alpha=.5, t='out_quad'))
        ).start(self)

    def refresh(self):
        self.fbo.draw()
        self.rc_back.clear()
        self.rc_front.clear()
        self.rc_line.clear()
        for child in self._children:
            self.create_3d_object(child)

    def on_object_thick(self, *args):
        self.refresh()

    def on_touch_down(self, touch):
        if 'scrollup' in touch.button:
            self.cam_dist += 10
        elif 'scrolldown' in touch.button:
            self.cam_dist -= 10

    def on_touch_move(self, touch):
        self.cam_theta += touch.dx / float(self.width) * self.cam_sensitivity
        self.cam_phi += touch.dy / float(self.height) * self.cam_sensitivity

    def create_3d_object(self, widget, level=0):
        uid = widget.uid
        if uid not in self.hue_cache:
            hue = random() * 255.
            self.hue_cache[uid] = hue
        else:
            hue = self.hue_cache[uid]

        r, g, b = hsv_to_rgb(hue, .8, 1)
        r2, g2, b2 = hsv_to_rgb(hue, .4, .4)
        a = 1.0
        m = self.object_thick
        fmt = [
            ('v_pos', 3, 'float'),
            ('v_color', 4, 'float'),
            ('v_tc0', 2, 'float')]

        x1, y1 = widget.pos
        x2 = widget.right
        y2 = widget.top
        z1 = level
        z2 = level + m

        # dosen't work, with or without initial, for scatter >_>
        x1, y1 = widget.to_window(widget.x, widget.y)
        x2, y2 = widget.to_window(widget.right, widget.y)
        x3, y3 = widget.to_window(widget.right, widget.top)
        x4, y4 = widget.to_window(widget.x, widget.top)

        u, w = [float(x) for x in self.size]

        vertices_back = [
            x1, y1, z1, r2, g2, b2, a, x1 / u, y1 / w,
            x2, y2, z1, r2, g2, b2, a, x2 / u, y2 / w,
            x3, y3, z1, r2, g2, b2, a, x3 / u, y3 / w,
            x4, y4, z1, r2, g2, b2, a, x4 / u, y4 / w,
            x1, y1, z2, r, g, b, a, x1 / u, y1 / w,
            x2, y2, z2, r, g, b, a, x2 / u, y2 / w,
            x3, y3, z2, r, g, b, a, x3 / u, y3 / w,
            x4, y4, z2, r, g, b, a, x4 / u, y4 / w,
        ]
        indices_back = [
            0, 2, 1, 0, 3, 2,
            1, 2, 6, 1, 6, 5,
            0, 1, 5, 0, 5, 4,
            3, 0, 4, 3, 4, 7,
            2, 3, 7, 2, 7, 6
        ]

        vertices_front = vertices_back[-4 * 9:]
        vertices_front[3::9] = [1.] * 4
        vertices_front[4::9] = [1.] * 4
        vertices_front[5::9] = [1.] * 4
        indices_front = [0, 1, 2, 0, 2, 3]

        n = 0.1
        la = self.line_alpha
        vertices = [
            x1 - n, y1 - n, z1 - n, 1, 1, 1, la, 0, 0,
            x2 + n, y2 - n, z1 - n, 1, 1, 1, la, 0, 0,
            x3 + n, y3 + n, z1 - n, 1, 1, 1, la, 0, 0,
            x4 - n, y4 + n, z1 - n, 1, 1, 1, la, 0, 0,
            x1 - n, y1 - n, z2 + n, 1, 1, 1, la, 0, 0,
            x2 + n, y2 - n, z2 + n, 1, 1, 1, la, 0, 0,
            x3 + n, y3 + n, z2 + n, 1, 1, 1, la, 0, 0,
            x4 - n, y4 + n, z2 + n, 1, 1, 1, la, 0, 0,
        ]
        indices = [0, 1, 1, 2, 2, 3, 3, 0, 0, 5, 1, 5, 2, 6, 3, 7, 4, 5, 5, 6,
                6, 7, 7, 4]


        if m > 0:
            with self.rc_back:
                Mesh(vertices=vertices_back,
                     indices=indices_back,
                     fmt=fmt,
                     mode='triangles')

        with self.rc_front:
            Mesh(vertices=vertices_front,
                 indices=indices_front,
                 fmt=fmt,
                 mode='triangles',
                 texture=self.fbo.texture)

        with self.rc_line:
            Mesh(vertices=vertices, indices=indices, mode='lines', fmt=fmt)


        # recurse
        for child in widget.children:
            self.create_3d_object(child, level + m)

    def setup_gl_context(self, *args):
        if self.object_thick > 1:
            glEnable(GL_DEPTH_TEST)

    def reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)

    def update_glsl(self, *largs):
        w, h = self.size
        w /= 2.
        h /= 2.
        #proj = Matrix().view_clip(-w, w, -h, h, 1, 1000, 1)
        proj = Matrix()
        proj.perspective(30., w / h, 1, 1000)

        # calculate camera view (should be outside glsl)
        d = self.cam_dist
        theta = self.cam_theta
        phi = self.cam_phi
        cx = cos(theta) * sin(phi) * d
        cy = cos(phi) * d
        cz = sin(theta) * sin(phi) * d

        model = Matrix().look_at(cx, cy, cz, 0, 0, 0, 0., 1., 0.)
        self.rc['projection_mat'] = proj
        self.rc['modelview_mat'] = model
        self.rc['diffuse_light'] = (1.0, 1.0, 0.8)
        self.rc['ambient_light'] = (0.1, 0.1, 0.1)

    def restore_content(self, *args):
        Clock.unschedule(self.update_glsl)
        win = self.win
        win.remove_widget(self)
        canvas = self.canvas
        self.canvas = self.fbo
        for child in self._children:
            self.remove_widget(child)
            win.add_widget(child)
        self.canvas = canvas

    def on_activated(self, instance, activated):
        if activated:
            self.create_3d()
        else:
            self.anim_to_restore_content()

    def anim_to_restore_content(self):
        cam_dist = self.property('cam_dist').defaultvalue
        cam_theta = self.property('cam_theta').defaultvalue
        cam_phi = self.property('cam_phi').defaultvalue
        object_thick = self.property('object_thick').defaultvalue
        line_alpha = self.property('line_alpha').defaultvalue
        anim =(Animation(cam_theta=cam_theta, cam_phi=cam_phi, t='out_quad') &
               Animation(cam_dist=cam_dist, object_thick=object_thick,
                   line_alpha=line_alpha,
                    t='in_out_quad'))
        anim.bind(on_complete=lambda *x:
                Clock.schedule_once(self.restore_content, 0))
        anim.start(self)

    def keyboard_shortcut(self, win, scancode, *largs):
        modifiers = largs[-1]
        # control+j
        if scancode == 106 and modifiers == ['ctrl']:
            self.activated = not self.activated
            return True
        elif scancode == 27:
            if self.activated:
                self.activated = False
                return True

        #print scancode, self.activated
        if not self.activated:
            return
        if scancode == 49:
            self.object_thick += 1
        elif scancode == 50:
            self.object_thick -= 1
        elif scancode == 32:
            self.refresh()


def create_inspector(win, ctx, *l):
    # Dunno why, but if we are creating inspector within the start(), no lang
    # rules are applied.
    ctx.inspector = Inspector3d(win=win)
    win.bind(on_keyboard=ctx.inspector.keyboard_shortcut)

def start(win, ctx):
    Clock.schedule_once(partial(create_inspector, win, ctx))


def stop(win, ctx):
    win.remove_widget(ctx.inspector)


from kivy.core.window import Window
from kivy.app import App
from kivy.uix.button import Button

from kivy.logger import Logger
Logger.setLevel('DEBUG')

class Demo(App):
    def build(self):
        button = Button(text="Test")
        create_inspector(Window, button)
        return button

Demo().run()
