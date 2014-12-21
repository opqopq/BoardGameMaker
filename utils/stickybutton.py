"A button that fire its on_press if touch remains down for self.repeat_interval seconds"

from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.properties import NumericProperty

class StickyButton(Button):
    repeat_interval= NumericProperty(.1)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            #schedule on press
            Clock.schedule_interval(self.on_press, self.repeat_interval)
        return super(StickyButton, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        Clock.unschedule(self.on_press)
        return super(StickyButton,self).on_touch_up(touch)