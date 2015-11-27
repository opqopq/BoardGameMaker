__author__ = 'opq'

from kivy.properties import *
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.vector import Vector
from kivy.uix.scatter import Scatter
from kivy.uix.scatterlayout import ScatterLayout
from kivy.animation import Animation
from kivy.base import runTouchApp
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.uix.carousel import Carousel
from kivy.core.window import Window


kv = """
<MagicScatter>:
    do_translation: False
    do_rotation: False
    do_scale: False
    selected: False
    canvas.before:
        Color:
            rgba: (0,0,0,1) if self.manager.activated else (0,0,0,0)
        Rectangle:
            size: self.size

    canvas.after:
        Color:
            rgba: (1,1,0,1) if self.manager.activated and self.selected else (0,0,0,0)
        Line:
            rectangle: self.x, self.y, self.scale*self.children[0].width if self.children else 0,self.scale*self.children[0].height if self.children else 0
            width: 3
            dash_offset: 3
            dash_length: 5

<VirtualScreenManagerBase>:
    canvas.before:
        Color:
            rgba: self.background_color  if self.activated else (0,0,0,0)
        Rectangle:
            size: self.size
            pos: self.pos

<VirtualScreenManagerGrid>:
    Label:
        text: root.current_screen.name if root.activated else ""
        font_size: 64
        size_hint: 1, None
        pos_hint: {'top':.99}

"""

Builder.load_string(kv)


class MagicScatter(ScatterLayout):
    manager = ObjectProperty()
    screen_name = StringProperty()
    wrapped = ObjectProperty()

    def on_touch_down(self, touch):
        button = getattr(touch, 'button', -1)
        if self.manager.activated and button == "left":
            if self.collide_point(*touch.pos):
                self.manager.current_screen = self.wrapped
                self.manager.activated = False #trigger the othrs tuff
                return True
        return Scatter.on_touch_down(self, touch)


class VirtualScreenManagerBase(FloatLayout):
    content = ListProperty()
    wrappers = DictProperty()
    current_screen = ObjectProperty(rebind=True)
    activated = BooleanProperty(False)
    use_keyboard_shortcut = BooleanProperty(False)
    scancode = NumericProperty()
    modifiers = ListProperty()
    spacing = NumericProperty()
    background_color = ListProperty([.5,.5,.5,1])

    def __init__(self, *args, **kwargs):
        FloatLayout.__init__(self, *args, **kwargs)
        self._keyboard = None
        from kivy.clock import Clock
        def shortcut(*largs):
            if self.use_keyboard_shortcut:
                def keyboard_shortcut(win, scancode, *largs):
                    modifiers = largs[-1]
                    ##print win, scancode, largs
                    #alt cmd start the magical tour
                    ##print 'scancode', scancode, scancode == self.scancode
                    ##print 'modifiers', self.modifiers,'in', modifiers, (set(self.modifiers) in set(modifiers) or ( modifiers == self.modifiers))
                    if scancode == self.scancode and  (set(self.modifiers) in set(modifiers) or ( modifiers == self.modifiers)):
                        self.activated = not self.activated
                from kivy.core.window import Window
                Window.bind(on_keyboard=keyboard_shortcut)
        Clock.schedule_once(shortcut, 1)

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        #print 'Got the following args', keyboard, keycode, text, modifiers
        key = keycode[1]
        if key in ('enter', 'spacebar', 'return'):
            keyboard.release()
            self.activated = False
        elif key in ('left','right','up','down'):
            index = self.content.index(self.current_screen)
            if key == 'right':
                index+=1
            elif key == 'left':
                index-=1
            elif key == 'up':
                index+=2
            elif key == 'down':
                index-=2
            index = index%len(self.content)
            self.wrappers[self.current_screen].selected = False
            self.current_screen = self.content[index]
            self.wrappers[self.current_screen].selected = True
        return True

    def on_activated(self, *args):
        if self.activated:
            #Request keyboard and listen for enter/space
            from kivy.core.window import Window
            self._keyboard = Window.request_keyboard(None, self, 'text')
            self._keyboard.bind(on_key_down=self._on_keyboard_down)
        else:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard = None

    def add_widget(self, widget, index=0, screen_name= ""):
        self.content.append(widget)
        if len(self.content) == 1:
            super(VirtualScreenManagerBase, self).add_widget(widget, index)
            self.current_screen = widget
        else:
            widget.parent = self

    def restore_widget(self, widget):
        if widget not in self.content:
            raise ValueError('Widget %s is not currently a child of %s'%(widget,self))
        super(VirtualScreenManagerBase,self).add_widget(widget)

    def restore_wrappers(self):
        for wrapper in self.wrappers.values():
            super(VirtualScreenManagerBase,self).add_widget(wrapper)

    def on_touch_down(self, touch):
        button = getattr(touch, 'button', "")
        if self.activated and button.startswith('scroll'):
            index = self.content.index(self.current_screen)
            if button == 'scrolldown':
                index+=1
            else:
                index-=1
            index = index%len(self.content)
            self.wrappers[self.current_screen].selected = False
            #print "SCI", self.content[index], self.content[index].__class__
            self.current_screen = self.content[index]
            self.wrappers[self.current_screen].selected = True
        return super(VirtualScreenManagerBase, self).on_touch_down(touch)


class VirtualScreenManagerGrid(VirtualScreenManagerBase):

    def on_activated(self,*args):
        super(VirtualScreenManagerGrid, self).on_activated(*args)
        if self.activated:
            for wrapper in self.wrappers.values():
                self.remove_widget(wrapper)
            self.restore_wrappers()
            from math import sqrt
            #Split between rows and cols, with one bigger than the other depending on windows size
            num_cols = int(sqrt(len(self.wrappers)))
            num_rows = int(float(len(self.wrappers))/num_cols) +1
            if Window.height>Window.width:
                num_cols, num_rows = num_rows, num_cols
            positions = list()
            for rindex in range(num_rows):
                for cindex in range(num_cols):
                    positions.append(Vector( cindex*float(1)/num_cols , rindex*float(1)/num_rows))
            scaler = Vector(num_cols,num_rows)
            WW = float(self.width - (scaler[0]+1)*self.spacing)/scaler[0] / self.width
            WH = float(self.height - (scaler[1]+1)*self.spacing)/scaler[1] / self.height
            SCALE = min(WW,WH)
            padding_x = (self.width - (self.spacing + self.width*SCALE)*num_cols)/2
            padding_y = (self.height - (self.spacing + self.height*SCALE)*num_rows)/2
            #print 'Paddings', padding_x, padding_y
            for position, screen in zip(positions,self.content):
                wrapper = self.wrappers[screen]
                wrapper.size_hint = None, None
                wrapper.size = self.size
                size = Vector(self.size)
                x,y = size * position
                x+= padding_x/2
                y+= padding_y/2
                if screen == self.current_screen:
                    #x,y animtion should have higher duration than scale, to make sure the pos is achieved
                    reducer = Animation(scale=SCALE, duration=.4)
                    reducer.start(wrapper)
                    reducer2 = Animation(x=x, y=y, duration=.42)
                    reducer2.start(wrapper)
                    wrapper.selected = True
                else:
                    wrapper.scale = SCALE
                    wrapper.x = x
                    wrapper.y = y
                    wrapper.selected = False
        else:
            for screen in self.wrappers:
                wrapper = self.wrappers[screen]
                if screen == self.current_screen:
                    w= self.wrappers[self.current_screen]
                    #x,y animtion should have higher duration than scale, to make sure the pos is achieved
                    expander =Animation(x=0, y=0, duration=.22)
                    expander2 = Animation(scale=1, duration=.2)
                    expander2.start(wrapper)
                    expander.start(wrapper)
                    wrapper.size_hint = 1,1
                    continue
                self.remove_widget(wrapper)

            #self.add_widget(self.current_screen)

    def set_screen(self, screenName):
        screen = None
        for c in self.content:
            if c.name == screenName:
                screen = c
                break
        #screen = self.screen_names[screenName]
        if screen == self.current_screen:
            return
        self.remove_widget(self.wrappers[self.current_screen])
        super(VirtualScreenManagerBase,self).add_widget(self.wrappers[screen])
        self.current_screen = screen
        wrapper = self.wrappers[screen]
        wrapper.scale = 1
        wrapper.pos = 0, 0
        wrapper.size_hint = 1, 1

    def add_widget(self, widget, index=0, screen_name = ""):
        if not len(self.children):
            #It is the label
            return super(VirtualScreenManagerBase, self).add_widget(widget, index)
        #Normal case
        if widget in self.wrappers:
            wrapper = self.wrappers[widget]
        else:
            self.content.append(widget)
            wrapper = MagicScatter(manager=self, screen_name=screen_name, wrapped = widget)
            widget.size_hint = 1,1
            wrapper.add_widget(widget)
            self.wrappers[widget] = wrapper
            widget.size = wrapper.size = self.size
            #print "Addition",widget, wrapper, widget.size, wrapper.size, widget.pos, wrapper.pos, screen_name
        if len(self.content) == 1:
            super(VirtualScreenManagerBase, self).add_widget(wrapper, index)
            self.current_screen = widget


class MagicLabel(Label):
    target = ObjectProperty()

    def on_touch_down(self, touch):
        #print 'ML tD',self.target.children[0], "Collide:",self.collide_point(*touch.pos)
        if self.collide_point(*touch.pos):
            if self.target:
                self.target.manager.current_screen = self.target.wrapped
                self.target.manager.activated = False #trigger the othrs tuff
                return True
        return Label.on_touch_down(self, touch)


class VirtualScreenManagerStack(VirtualScreenManagerBase):
    "Same as above, but display the virtual screens as a scrollable list"
    orientation = OptionProperty('vertical', options=['vertical','horizontal'])

    def on_activated(self,*args):
        super(VirtualScreenManagerStack, self).on_activated(*args)
        print 'on activated', self.activated, self.current_screen
        SCALE = .6 if self.activated else 1
        if self.activated:
            self.clear_widgets()
            grid = Carousel(size_hint = (1,1), width=.8*Window.width, x=.1*Window.width, direction="bottom")
            FloatLayout.add_widget(self,grid)
        for wrapper in self.wrappers.values():
            print 'before', wrapper.size
            wrapper.scale=SCALE
            print 'after', wrapper.size
            if self.activated:
                wrapper.size_hint= None, None
                print 'adding wrapper of ', wrapper.height
                grid.add_widget(wrapper)
            else:
                self.children[0].remove_widget(wrapper)
        if not self.activated:
            self.clear_widgets()
            w= self.wrappers[self.current_screen]
            w.pos = 0,0
            w.size_hint= 1,1
            FloatLayout.add_widget(self, w)
        else:
            print "grid", grid.size, grid.pos, grid.size_hint
        return
        if 0:
            self.clear_widgets()
            sv = ScrollView()
            with sv.canvas.before:
                Color(.3,.3,.3)
                Rectangle(size=self.size, pos=self.pos)
            FloatLayout.add_widget(self,sv)
            grid= GridLayout()
            sv.do_scroll_x = self.activated
            sv.do_scroll_y = self.activated
            grid.rows = 1 if self.orientation=='horizontal' else None
            grid.cols = 1 if self.orientation=="vertical" else None
            grid.bind(minimum_height = grid.setter('height'))
            grid.bind(minimum_width = grid.setter('width'))
            grid.spacing = self.spacing
            sv.add_widget(grid)
            SCALE = .6
                        # if self.orientation == 'vertical':
                        #     attrName = "cols"
                        #     dh_name = "row_default_height"
                        #     default_value = SCALE*self.height #300
                        #     size_hint=(1,None)
                        # else:
                        #     attrName = "rows"
                        #     dh_name = "col_default_width"
                        #     default_value = 400
                        #     size_hint=(None,1)
                        # kwargs = {attrName:2, dh_name:default_value}
                        # kwargs = {attrName:2}
                        # kwargs = {attrName:1}
                        # kwargs = {attrName:1, dh_name:default_value}
                        # if self.orientation == 'vertical':
                        #     grid.height = len(self.content)*(SCALE*self.height+self.spacing)
                        # else:
                        #     grid.width = len(self.content)*(SCALE*self.width + self.spacing)
            for sindex, screen in enumerate(self.content):
                wrapper = self.wrappers[screen]
                wrapper.size_hint = None,None
                wrapper.size = self.size
                if 1 or screen != self.current_screen:
                    wrapper.scale = SCALE
                else:
                    reducer = Animation(scale=SCALE, opacity=.5, duration=.3)
                    reducer.start(wrapper)
                grid.add_widget(wrapper)
                #Clock.schedule_once(adder,.31)
                #if self.orientation=='vertical':
                #    name = wrapper.screen_name or str(screen)
                #    grid.add_widget(MagicLabel(target= wrapper, text=name, size = wrapper.size, texture_size = (800,600), size_hint_x=None, width=60))
            ##if self.orientation =="horizontal":
            ##    for screen in self.content:
            ##        name = wrapper.screen_name or str(screen)
            ##        grid.add_widget(MagicLabel(target= wrapper, text=name, size = wrapper.size, texture_size = (800,600), size_hint_y=None, height=30))
            #scrool sv to proper height
            ##if self.orientation=="vertical":
            ##    sv.scroll_y= 1- float(self.content.index(self.current_screen))/len(self.content)
            ##else:
            ##    sv.scroll_x= float(self.content.index(self.current_screen))/len(self.content)

        else:
            sv = self.children[0]
            grid = sv.children[0]
            for screen in self.content:
                wrapper = self.wrappers[screen]
                grid.remove_widget(wrapper)
            self.clear_widgets()
            w = self.wrappers[self.current_screen]
            w.size_hint = 1,1
            FloatLayout.add_widget(self,w)
            wrapper = self.wrappers[self.current_screen]
            expander = Animation(scale = 1, opacity=1, x=0, y=0, duration=.3)
            expander.start(wrapper)

    def add_widget(self, widget, index=0, screen_name= ""):
        if not len(self.children):
            #It is the label
            return super(VirtualScreenManagerBase, self).add_widget(widget, index)
        #Normal case
        if widget in self.wrappers:
            wrapper = self.wrappers[widget]
        else:
            self.content.append(widget)
            wrapper = MagicScatter(manager=self, screen_name=screen_name, wrapped = widget)
            widget.size_hint = 1,1
            wrapper.add_widget(widget)
            self.wrappers[widget] = wrapper
            widget.size = wrapper.size = self.size
            #print "Addition",widget, wrapper, widget.size, wrapper.size, widget.pos, wrapper.pos
        if len(self.content) == 1:
            super(VirtualScreenManagerBase, self).add_widget(wrapper, index)
            self.current_screen = widget

if __name__ == '__main__':
    from kivy.logger import Logger
    Logger.setLevel('DEBUG')
    try:
        from kivy.factory import Factory
        vskv = """
<VirtualScreen@BoxLayout>:
    orientation: "vertical"
    Button:
        text: "Activate"
        size_hint_y: None
        height: 40
        on_press: content.activated = not content.activated
        canvas.before:
            Color:
                rgb: 0,1,0
            Rectangle:
                size: self.size
                pos: self.pos

    VirtualScreenManagerStack:
        id: content
        size: root.size
        #spacing: 10
        orientation: "horizontal"
"""
        Builder.load_string(vskv)
        vs = Factory.get('VirtualScreen')()
        root = vs.ids.content #VirtualScreenManagerStack()
        from kivy.uix.button import Button
        from kivy.clock import Clock
        import os
        os.chdir('..')
        from console import BGConsole
        from deck import BGDeckMaker
        from layout import BGLayoutMaker
        from old.geekbrowser import BGGeekBrowser
        root.add_widget(BGDeckMaker(),screen_name="DeckMaker")
        root.add_widget(BGLayoutMaker())
        root.add_widget(BGConsole())
        root.add_widget(BGGeekBrowser())
        runTouchApp(vs)
    except Exception,e:
        import traceback
        traceback.print_exc()