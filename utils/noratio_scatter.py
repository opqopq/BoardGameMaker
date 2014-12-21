__author__ = 'HO.OPOYEN'

from kivy.uix.scatter import Scatter
from math import radians
from kivy.properties import BooleanProperty, AliasProperty, NumericProperty, ReferenceListProperty
from kivy.vector import Vector
from kivy.graphics.transformation import Matrix
from kivy.lang import Builder

Builder.load_string('''
<NoRatioScatter>:
    do_rotation: False
''')

class NoRatioScatter(Scatter):
    '''No Ratio Scatter class.
    Scatter than can be extended differently from X or Y value, depending on the do_keep_ratio
    '''

    do_keep_ratio = BooleanProperty(False)
    "Allow scaling in both X/Y direction is set to True"

    do_scale_x = BooleanProperty(True)
    do_scale_y = BooleanProperty(True)

    def _get_do_scale(self):
        return (self.do_scale_x, self.do_scale_y)

    def _set_do_scale(self, value):
        if type(value) in (list, tuple):
            self.do_scale_x, self.do_scale_y = value
        else:
            self.do_scale_x = self.do_scale_y = bool(value)

    do_scale = AliasProperty(_get_do_scale, _set_do_scale,bind=('do_scale_x', 'do_scale_y'))
    #"Allow scaling on the X or Y axis."

    scale_min_x = NumericProperty(0.01)
    scale_min_y = NumericProperty(0.01)

    def _get_scale_min(self):
        return (self.scale_min_x, self.scale_min_y)

    def _set_scale_min(self, value):
        if type(value) in (list, tuple):
            self.scale_min_x, self.scale_min_y = value
        else:
            self.scale_min_x = self.scale_min_y = bool(value)

    scale_min = AliasProperty(_get_scale_min, _set_scale_min, bind=('scale_min_x', 'scale_min_y'))
    #"Minimal scalling on the X or Y axis. Default to (0.01, 0.01)"


    scale_max_x = NumericProperty(1e20)
    scale_max_y = NumericProperty(1e20)

    def _get_scale_max(self):
        return (self.scale_max_x, self.scale_max_y)

    def _set_scale_max(self, value):
        if type(value) in (list, tuple):
            self.scale_max_x, self.scale_max_y = value
        else:
            self.scale_max_x = self.scale_max_y = bool(value)

    scale_max = AliasProperty(_get_scale_max, _set_scale_max,bind=('scale_max_x', 'scale_max_y'))
    #"maximal scalling on the X or Y axis. Default to (1e20,1e20)"


    def _get_scale_x(self):
        p1 = Vector(*self.to_parent(0, 0))
        p2 = Vector(*self.to_parent(1, 0))
        scale_x = p1.distance(p2)

        # XXX float calculation are not accurate, and then, scale can be
        # throwed again even with only the position change. So to
        # prevent anything wrong with scale, just avoid to dispatch it
        # if the scale "visually" didn't change. #947
        # Remove this ugly hack when we'll be Python 3 only.
        if hasattr(self, '_scale_px'):
            if str(scale_x) == str(self._scale_px):
                return self._scale_px

        self._scale_px = scale_x
        return scale_x

    def _set_scale_x(self, scale):
        rescale_x = scale * 1.0 / self.scale_x
        self.apply_transform(Matrix().scale(rescale_x, self.scale_y, rescale_x),
                             post_multiply=True,
                             anchor=self.to_local(*self.center))

    scale_x = AliasProperty(_get_scale_x, _set_scale_x, bind=('x', 'transform'))
    #"Scale X value of the scatter."

    def _get_scale_y(self):
        p1 = Vector(*self.to_parent(0, 0))
        p2 = Vector(*self.to_parent(0, 1))
        scale_y = p1.distance(p2)

        # XXX float calculation are not accurate, and then, scale can be
        # throwed again even with only the position change. So to
        # prevent anything wrong with scale, just avoid to dispatch it
        # if the scale "visually" didn't change. #947
        # Remove this ugly hack when we'll be Python 3 only.
        if hasattr(self, '_scale_py'):
            if str(scale_y) == str(self._scale_py):
                return self._scale_py

        return scale_y

    def _set_scale_y(self, scale):
        rescale_y = scale * 1.0 / self.scale_y
        self.apply_transform(Matrix().scale(self.scale_x, rescale_y, rescale_y), post_multiply=True, anchor=self.to_local(*self.center))

    scale_y = AliasProperty(_get_scale_y, _set_scale_y, bind=('y', 'transform'))
    #"Scale Y value of the scatter."


    scale = ReferenceListProperty(scale_x, scale_y)

    def transform_with_touch(self, touch):
        # just do a simple one finger drag
        changed = False
        if len(self._touches) == self.translation_touches:
            # _last_touch_pos has last pos in correct parent space,
            # just like incoming touch
            dx = (touch.x - self._last_touch_pos[touch][0]) * self.do_translation_x
            dy = (touch.y - self._last_touch_pos[touch][1]) * self.do_translation_y
            dx = dx / self.translation_touches
            dy = dy / self.translation_touches
            self.apply_transform(Matrix().translate(dx, dy, 0))
            changed = True

        if len(self._touches) == 1:
            return changed

        # we have more than one touch... list of last known pos
        points = [Vector(self._last_touch_pos[t]) for t in self._touches
                  if t is not touch]
        # add current touch last
        points.append(Vector(touch.pos))

        # we only want to transform if the touch is part of the two touches
        # farthest apart! So first we find anchor, the point to transform
        # around as another touch farthest away from current touch's pos
        anchor = max(points[:-1], key=lambda p: p.distance(touch.pos))

        # now we find the touch farthest away from anchor, if its not the
        # same as touch. Touch is not one of the two touches used to transform
        farthest = max(points, key=anchor.distance)
        if farthest is not points[-1]:
            return changed

        # ok, so we have touch, and anchor, so we can actually compute the
        # transformation
        old_line = Vector(*touch.ppos) - anchor
        new_line = Vector(*touch.pos) - anchor
        if not old_line.length():   # div by zero
            return changed

        angle = radians(new_line.angle(old_line)) * self.do_rotation
        self.apply_transform(Matrix().rotate(angle, 0, 0, 1), anchor=anchor)

        if self.do_scale_x or self.do_scale_y:
            try:
                scale_x = Vector(new_line[0],0).length()/Vector(old_line[0],0).length()
            except ZeroDivisionError:
                scale_x = 1
            try:
                scale_y = Vector(0,new_line[1]).length()/Vector(0,old_line[1]).length()
            except ZeroDivisionError:
                scale_y = 1
            ##scale = new_line.length() / old_line.length()
            new_scale_x = scale_x * self.scale[0]
            new_scale_y = scale_y * self.scale[1]
            ##new_scale = scale * self.scale

            if new_scale_x < self.scale_min[0]:
                scale_x = self.scale_min[0] / self.scale[0]
            elif new_scale_x > self.scale_max[0]:
                scale_x = self.scale_max[0] / self.scale[0]
            if new_scale_y < self.scale_min[1]:
                scale_y = self.scale_min[1] / self.scale[1]
            elif new_scale_y > self.scale_max[1]:
                scale_y = self.scale_max[1] / self.scale[1]

            self.apply_transform(Matrix().scale(scale_x, scale_y, scale_x), anchor=anchor)
            changed = True
        return changed

    def on_touch_down(self, touch):
        x, y = touch.x, touch.y

        # if the touch isnt on the widget we do nothing
        if not self.do_collide_after_children:
            if not self.collide_point(x, y):
                return False

        # let the child widgets handle the event if they want
        touch.push()
        touch.apply_transform_2d(self.to_local)
        if super(Scatter, self).on_touch_down(touch):
            # ensure children don't have to do it themselves
            if 'multitouch_sim' in touch.profile:
                touch.multitouch_sim = True
            touch.pop()
            self._bring_to_front(touch)
            return True
        touch.pop()

        # if our child didn't do anything, and if we don't have any active
        # interaction control, then don't accept the touch.
        if not self.do_translation_x and \
                not self.do_translation_y and \
                not self.do_rotation and \
                not self.do_scale_x and \
                not self.do_scale_y:
            return False

        if self.do_collide_after_children:
            if not self.collide_point(x, y):
                return False

        if 'multitouch_sim' in touch.profile:
            touch.multitouch_sim = True
        # grab the touch so we get all it later move events for sure
        self._bring_to_front(touch)
        touch.grab(self)
        self._touches.append(touch)
        self._last_touch_pos[touch] = touch.pos

        return True


if __name__ == '__main__':
    from kivy.logger import Logger
    Logger.setLevel("WARNING")
    from kivy.base import runTouchApp
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.image import Image
    fl = FloatLayout()
    a= NoRatioScatter()
    img = Image(source='images/judge.jpg')
    fl.add_widget(a)
    a.add_widget(img)

    runTouchApp(fl)