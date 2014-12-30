"Contains the different value/property editor widget & mecanism"
__author__ = 'opq'

from kivy.lang import Builder
from os.path import isfile
from kivy.metrics import cm
from kivy.properties import *
from kivy.vector import Vector
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup

Builder.load_file('kv/editors.kv')

###############################################
#        Editor                               #
###############################################

class Editor:
    widget = ObjectProperty(None)

    def __init__(self, target):
        self.target = target

    def export(self):
        return self.widget.target_key, self.widget.stored_value, self.widget.target_attr

    def create(self, name, keyname, **kwargs):
        self.widget = self.getWidgets(name, keyname, **kwargs)
        return self.widget

class ColorEditor(Editor):
    def getWidgets(self,name, keyname, **kwargs):
        t=Button(text="Choose", **kwargs)
        #Create a callback for the modal frame
        def cb(instance):
            #Display yhe coice
            setattr(self.target, keyname, instance.ids.cpicker.color)
            #Save the choice for later use
            t.stored_value = instance.ids.cpicker.color
            t.background_color = instance.ids.cpicker.color
            # from kivy.graphics import Color, Rectangle
            # with t.canvas.before:
            #     Color(*instance.ids.cpicker.color)
            #     Rectangle(pos= t.pos, size= t.size)

        #Create callback for button that would start a modal
        def button_callback(instance):
            from kivy.core.window import Window
            cp_width = min(Window.size)*.8
            cp_pos = [(Window.size[0]-cp_width)/2,(Window.size[1]-cp_width)/2]
            popup = ColorEditorPopup(name=name, path=".", color=getattr(self.target, keyname), pos=cp_pos, size=(cp_width,cp_width), cb=cb)
            #popup.bind(on_dismiss=cb)
            popup.open()
        #Assign it
        t.bind(on_press=button_callback)
        t.stored_value = None
        t.target_key = keyname
        t.target_attr = name
        return t

class BooleanEditor(Editor):
    def getWidgets(self, name, keyname, **kwargs):
        from kivy.uix.checkbox import CheckBox
        from kivy.uix.switch import Switch
        #t = CheckBox(active = getattr(self.target, keyname))
        t = Switch(active = getattr(self.target, keyname))
        def cb(instance,value):
            setattr(self.target, keyname,value)
            t.stored_value = value
        t.bind(active=cb)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t

class TextEditor(Editor):
    def getWidgets(self, name, keyname, **kwargs):
        #can not use getattr with kivy property
        ml_value = '\n' in getattr(self.target, keyname)
        t=TextInput(text=str(getattr(self.target, keyname)), multiline=ml_value)
        def cb(instance,value):
            setattr(self.target, keyname, value)
            #self.target.text = value
            t.stored_value = value
        t.bind(text=cb)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t

class ListEditor(Editor):
    def getWidgets(self, name, keyname, **kwargs):
        #can not use getattr with kivy property
        t=TextInput(text=", ".join(getattr(self.target, keyname)))
        def cb(instance,value):
            setattr(self.target, keyname, value.split(','))
            t.stored_value = value.split(',')
        t.bind(text=cb)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t

class TransfoListEditor(Editor):
    def getWidgets(self, name, keyname, **kwargs):
        t=Button(text="Define")
        def cbimg(value):
            try:
                setattr(self.target, keyname, value)
                t.stored_value = value
            except ValueError,E:
                from conf import log
                log(E)
        t.bind(text=cbimg)
        def button_callback(instance):
            from kivy.core.window import Window
            cp_width = min(Window.size)
            size = Vector(Window.size)*.9
            title = 'Choose Transformation for %s'%name
            popup = DictChoiceEditorPopup(title=title, name=name, size=size, pos=(0,0), cb=cbimg, keyname = getattr(self.target, keyname))
            from img_xfos import xfos
            popup.load_items(xfos)
            popup.load_choices(self.target.xfos)
            popup.open()
        t.bind(on_press= button_callback)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t

class IntEditor(TextEditor):
    def getWidgets(self, name, keyname, **kwargs):
        t=TextInput(text=str(getattr(self.target, keyname)))
        def cb(instance,value):
            try:
                setattr(self.target, keyname, int(value))
                t.stored_value = int(value)
            except ValueError,E:
                from conf import log
                log(E)
        t.bind(text=cb)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        #Xross Bind
        def xcb(*args):
            t.text = str(getattr(self.target, keyname))
        args={keyname:xcb}
        self.target.bind(**args)
        return t

class AdvancedIntEditor(IntEditor):
    def getWidgets(self, name, keyname, **kwargs):
        from kivy.uix.boxlayout import BoxLayout
        from utils.stickybutton import StickyButton

        ti = IntEditor.getWidgets(self, name, keyname, **kwargs)
        ti.size_hint_x = .5
        t = BoxLayout(orientation = 'horizontal')
        vb = BoxLayout(orientation = 'vertical', size_hint=(None,None), size=(15,36))

        t.add_widget(ti)
        t.add_widget(vb)

        pb = StickyButton(text="^",background_color=(1,1,1,1),size_hint=(None,None), size=(15,17))
        mb = StickyButton(text="v", background_color = (1,0,1,1),size_hint=(None,None), size=(15,17))


        def pb_cb(*args):
            setattr(self.target, keyname, int(ti.text)+1)
            t.stored_value+=1

        def mb_cb(*args):
            setattr(self.target, keyname, int(ti.text)-1)
            t.stored_value-=1

        pb.on_press = pb_cb
        mb.on_press = mb_cb

        vb.add_widget(pb)
        vb.add_widget(mb)

        t.target_key = keyname
        t.stored_value = 0
        t.target_attr = name
        return t

class FloatEditor(IntEditor):
    def getWidgets(self, name, keyname, **kwargs):
        t=TextInput(text=str(getattr(self.target, keyname)))
        def cb(instance,value):
            try:
                setattr(self.target, keyname, float(value))
                t.stored_value = float(value)
            except ValueError,E:
                from conf import log
                log(E)
        t.bind(text=cb)
        t.target_key = keyname
        t.stored_value = 0
        t.target_attr = name
        #Xross Bind
        def xcb(*args):
            t.text = str(getattr(self.target, keyname))
        args={keyname:xcb}
        self.target.bind(**args)
        return t

class MetricEditor(Editor):
    def getWidgets(self, name, keyname, **kwargs):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.spinner import Spinner
        t = BoxLayout(orientation='horizontal')
        ti = TextInput(text=str(getattr(self.target, keyname)))
        ts = Spinner(text='px', values=('cm','px'), size_hint_x=None, width=40)
        t.add_widget(ti)
        t.add_widget(ts)
        def cb(instance, value):
            try:
                # First remove the binding to avoid update loop
                args={keyname:xcb}
                self.target.unbind(**args)
                if ts.text != "px":
                    setattr(self.target, keyname, int(round(float(value)*cm(1))))
                    t.stored_value = "'%s%s'"%(value,ts.text)
                else:
                    setattr(self.target, keyname, int(round(float(value))))
                    t.stored_value = int(round(float(value)))
                # Now, rebind it
                args = {keyname: xcb}
                self.target.bind(**args)
            except ValueError,E:
                from conf import log
                log(E)
                print E
        ti.bind(text=cb)
        def cbs(instance, theText):
            try:
                #Now we convert
                if theText == 'px':
                    ti.text = "%s"%(int(round(cm(1)*float(ti.text))))
                else:
                    ti.text= "%.2f"%(float(ti.text)/cm(1))
                #Here, put the change in the stored value but not on the template itself.
                #it breaks for scatter, but not for widget
                #no change in value <=> no settr ####setattr(self.target, keyname, "%s%s"%(ti.text,theText))
                t.stored_value= "%s%s"%(ti.text,theText)
            except ValueError,E:
                from conf import log
                log(E)
                print E
        ts.bind(text=cbs)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        #Xross Bind
        def xcb(*args):
            #print 'scb called', ti.text, getattr(self.target, keyname)
            res= getattr(self.target, keyname)
            if ts.text != 'px':
                res = "%.2f"%(res/cm(1))
            else:
                res = "%.2f"%res
            ti.text = res
        args={keyname:xcb}
        self.target.bind(**args)
        return t

class BorderEditor(Editor):
    def getWidgets(self, name, keyname, **kwargs):
        t = TextInput(text=str(self.target.border_width), **kwargs)
        t.target_key = keyname
        def cb(instance,value):
            instance.background_color=1,1,1,1
            try:
                t.stored_value = int(value)
                setattr(self.target,keyname,int(value))
            except ValueError:
                t.background_color=1,0,0,1
        t.bind(text=cb)
        t.target_key = keyname
        t.target_attr = name
        t.stored_value =  None
        return t

class FileEditor(Editor):
    def getWidgets(self, name, keyname, **kwargs):
        from os.path import split
        t=Button(text="...", **kwargs)
        #Create a callback for the modal frame
        def cbimg(instance):
            s = instance.ids.fpicker.selection
            if len(s) and isfile(s[0]):
                setattr(self.target, keyname, s[0])
                t.stored_value = instance.ids.fpicker.selection[0]
                t.text = split(s[0])[-1]
            else:
                t.text="..."
        #Create callback for button that would start a modal
        def button_callback(instance):
            from kivy.core.window import Window
            cp_width = min(Window.size)
            size = Vector(Window.size)*.9
            cp_pos = [(Window.size[0]-cp_width)/2,(Window.size[1]-cp_width)/2]
            filters = getattr(self.target, '%s_filters'%keyname, [])
            #filters= ['*.jpg', '*.png','*.jpeg','*.gif']
            popup = FileEditorPopup(name=name, size=size, pos=(0,0), cb=cbimg, filters=filters )
            popup.open()
        t.bind(on_press=button_callback)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t

class SubImageEditor(Editor):
    def getWidgets(self, name, keyname, **kwargs):
        t=Button(text="...", **kwargs)
        #Create a callback for the modal frame
        def cbimg(instance):
            s = instance.ids
            if s.fpicker.selection:
                setattr(self.target, keyname, [s.fpicker.selection[0], float(s.img_x.text),float(s.img_y.text), float(s.img_width.text), float(s.img_height.text)])
                t.stored_value = [s.fpicker.selection[0], float(s.img_x.text),float(s.img_y.text), float(s.img_width.text), float(s.img_height.text)]
        #Create callback for button that would start a modal
        def button_callback(instance):
            from kivy.core.window import Window
            cp_width = min(Window.size)
            size = Vector(Window.size)*.9
            #cp_pos = [(Window.size[0]-cp_width)/2,(Window.size[1]-cp_width)/2]
            popup = SubImageEditorPopup(name=name, size=size, pos=(0,0), cb=cbimg, keyname = getattr(self.target, keyname))
            dimension = getattr(self.target, keyname)
            from os.path import split
            popup.ids.fpicker.path = split(dimension[0])[0] if dimension[0] else "."
            #popup.ids.fpicker.selection = [split(dimension[0])[1]]
            if isfile(dimension[0]):
                popup.ids.img.source = dimension[0]
            from kivy.clock import Clock
            def mover(*args):
                overlay = popup.ids.overlay
                img = popup.ids.img
                popup.ids.tabpanel.switch_to(popup.ids.content.__self__)
                overlay.size =(img.height * img.image_ratio, img.height)
                overlay.pos = (img.x + (img.width-overlay.width)/2, img.y)
                popup.ids.img_x.text = str(dimension[1])
                popup.ids.img_y.text = str(dimension[2])
                popup.ids.img_width.text = str(dimension[3])
                popup.ids.img_height.text = str(dimension[4])
            Clock.schedule_once(mover,.1)
            popup.open()
        t.bind(on_press=button_callback)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t

class RangeEditor(Editor):
    def getWidgets(self, name, keyname, **kwargs):
        from kivy.uix.slider import Slider
        range= getattr(self.target, '%s_range'%keyname, [0, 1.0])
        t=Slider(range=range, value = getattr(self.target, keyname))
        def cb(instance,value):
            try:
                setattr(self.target, keyname, value)
                t.stored_value = value
            except ValueError,E:
                from conf import log
                log(E)
        t.bind(value=cb)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t

class AdvancedRangeEditor(RangeEditor):
    def getWidgets(self, name, keyname, **kwargs):
        from kivy.uix.textinput import TextInput
        from kivy.uix.boxlayout import BoxLayout
        from utils.stickybutton import StickyButton
        r = RangeEditor.getWidgets(self, name, keyname, **kwargs)
        ti = TextInput(text = "%.2f"%getattr(self.target, keyname))
        ti.size_hint_x = .5
        t = BoxLayout(orientation = 'horizontal')

        def string_setter(instance, value):
            ti.text = "%.2f"%value
        r.bind(value= string_setter)

        def float_setter(instance, value):
            r.value = float(value)

        ti.bind(text = float_setter)

        t.add_widget(ti)
        t.add_widget(r)

        t.target_key = keyname
        t.stored_value = getattr(self.target, keyname)
        t.target_attr = name
        return t

class ChoiceEditor(Editor):
    def getWidgets(self, name, keyname, **kwargs):
        from kivy.uix.spinner import Spinner
        t=Spinner(values=getattr(self.target,'%s_values'%keyname), text = getattr(self.target, keyname))
        def cb(instance,value):
            try:
                setattr(self.target, keyname, value)
                t.stored_value = value
            except ValueError,E:
                from conf import log
                log(E)
        t.bind(text=cb)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t

from kivy.uix.spinner import SpinnerOption

class ColorOption(SpinnerOption):

    def __init__(self, **kwargs):
        super(SpinnerOption,self).__init__(**kwargs)
        from kivy.clock import Clock
        #wiat a little an hope daddy get me some choices
        Clock.schedule_once(self.on_choices)

    def on_choices(self, *args):
        if not self.choices:
            return
        #add some widget
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, Rectangle
        sw,sh= self.size
        cp = min(sh,sw)
        wid = Widget(size=(cp,cp), right=self.right-cp, y=self.y)
        with wid.canvas.before:
            Color(*self.choices[self.text])
            Rectangle(pos=wid.pos, size= wid.size)
        self.add_widget(wid)

class ColorOptionEditor(Editor):
    def getWidgets(self, name, keyname, **kwargs):
        from kivy.uix.spinner import Spinner
        t=Spinner(values=getattr(self.target,'%s_values'%keyname), text = getattr(self.target, keyname), option_cls = ColorOption)
        t.option_cls.choices = getattr(self.target, 'choices')
        def cb(instance,value):
            try:
                setattr(self.target, keyname, value)
                t.stored_value = value
            except ValueError,E:
                from conf import log
                log(E)
        t.bind(text=cb)
        #Cross bingding: when selection_values is changed,
        def xcb(*args):
            res= getattr(self.target, "%s_values"%keyname)
            t.values= res
            t.text = getattr(self.target, keyname)

        kv = {"%s_values"%keyname: xcb}
        self.target.bind(**kv)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t

class ImgOption(SpinnerOption):

    def __init__(self, **kwargs):
        super(SpinnerOption,self).__init__(**kwargs)
        from kivy.clock import Clock
        #wiat a little an hope daddy get me some choices
        Clock.schedule_once(self.on_choices)

    def on_choices(self, *args):
        if not self.choices:
            return
        #add some widget
        from kivy.uix.image import Image
        self.add_widget(Image(source=self.choices[self.text], size = self.size, pos = (self.x-self.width/4,self.y)))

class ImgOptionEditor(Editor):
    def getWidgets(self, name, keyname, **kwargs):
        from kivy.uix.spinner import Spinner
        t=Spinner(values=getattr(self.target,'%s_values'%keyname), text = getattr(self.target, keyname), option_cls = ImgOption)
        t.option_cls.choices = getattr(self.target, 'choices')
        def cb(instance,value):
            try:
                setattr(self.target, keyname, value)
                t.stored_value = value
            except ValueError,E:
                from conf import log
                log(E)
        t.bind(text=cb)
        #Cross bingding: when selection_values is changed,
        def xcb(*args):
            res= getattr(self.target, "%s_values"%keyname)
            t.values= res
            t.text = getattr(self.target, keyname)

        kv = {"%s_values"%keyname: xcb}
        self.target.bind(**kv)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t

class ImageChoiceEditor(Editor):
    def getWidgets(self, name, keyname, **kwargs):
        text = ""
        if self.target.choices:
            text= self.target.selection or self.target.choices.keys()[0]
        t=Button(text = "Define")
        def cbimg(value):
            try:
                setattr(self.target, keyname, value)
                t.stored_value = value
            except ValueError,E:
                from conf import log
                log(E)
        t.bind(text=cbimg)
        def button_callback(instance):
            from kivy.core.window import Window
            cp_width = min(Window.size)
            size = Vector(Window.size)*.9
            popup = ImageChoiceEditorPopup(name=name, size=size, pos=(0,0), cb=cbimg, keyname = getattr(self.target, keyname))
            popup.load_choices(self.target.choices)
            popup.open()
        t.bind(on_press= button_callback)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t

class ColorChoiceEditor(Editor):
    def getWidgets(self, name, keyname, **kwargs):
        text = ""
        if self.target.choices:
            text= self.target.selection or self.target.choices.keys()[0]
        t = Button(text="Define")

        def cbimg(value):
            try:
                setattr(self.target, keyname, value)
                t.stored_value = value
            except ValueError, E:
                from conf import log
                log(E)
        t.bind(text=cbimg)

        def button_callback(instance):
            from kivy.core.window import Window
            cp_width = min(Window.size)
            size = Vector(Window.size)*.9
            popup = ColorChoiceEditorPopup(name=name, size=size, pos=(0, 0), cb=cbimg, keyname = getattr(self.target, keyname))
            popup.load_choices(self.target.choices)
            popup.open()

        t.bind(on_press= button_callback)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t

class FontChoiceEditor(ChoiceEditor):

    def getWidgets(self, name, keyname, **kwargs):
        #Create Font Dir
        import os
        from kivy.utils import platform
        from os.path import join

        if platform == 'linux':
            fdirs = ['/usr/share/fonts/truetype', '/usr/local/share/fonts', os.path.expanduser('~/.fonts'),        os.path.expanduser('~/.local/share/fonts')]
        elif platform == 'macosx':
            fdirs = ['/Library/Fonts', '/System/Library/Fonts',
                os.path.expanduser('~/Library/Fonts')]
        elif platform == 'win':
            fdirs = [os.environ['SYSTEMROOT'] + os.sep + 'Fonts']
        elif platform == 'ios':
            fdirs = ['/System/Library/Fonts']
        elif platform == 'android':
            fdirs = ['/system/fonts']
        from glob import glob
        fonts =  dict()
        fonts['DroidSans'] = 'DroidSans.ttf'
        for folder in fdirs:
            path = join(folder, '*.ttf')
            for x in glob(path):
                fonts[os.path.split(x)[-1]] = x
        t=Button(text="Define")
        def cbimg(popup):
            try:
                print 'popup fond editor', self.target, keyname, popup
                #Not a claisscal one. setattr for font_name, font_size, bold & italic
                #Create a fake value holder with name/size/bold/italic
                bold = popup.ids.cb_bold.active
                italic = popup.ids.cb_italic.active
                font_name = popup.ids.font_name.text
                font_size = int(popup.ids.font_size.text)
                setattr(self.target,'bold', bold)
                setattr(self.target,'italic', italic)
                setattr(self.target,'font_size', font_size)
                setattr(self.target,'font_name', font_name )
                t.stored_value = [font_name, font_size, bold, italic]
                setattr(self.target, 'font', t.stored_value)
            except ValueError,E:
                from conf import log
                log(E)
        t.bind(text=cbimg)

        font_name, font_size, bold, italic = getattr(self.target, keyname)

        def button_callback(instance):
            from kivy.core.window import Window
            cp_width = min(Window.size)
            size = Vector(Window.size)*.9
            title = 'Font Details for %s'%name
            popup = FontEditorPopup(title=title, name=name, size=size, pos=(0,0), cb=cbimg, font_name=font_name, font_size=font_size, bold=bold, italic=italic)
            popup.choices = fonts.keys()
            popup.open()
        t.bind(on_press=button_callback)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t


        t.bind(text=cb)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t

class EffectsEditor(Editor):
    def getWidgets(self, name, keyname, **kwargs):
        t=Button(text="Define")
        def cbimg(value):
            try:
                setattr(self.target, keyname, value)
                t.stored_value = value
            except ValueError,E:
                from conf import log
                log(E)
        t.bind(text=cbimg)
        def button_callback(instance):
            from kivy.core.window import Window
            cp_width = min(Window.size)
            size = Vector(Window.size)*.9
            title = 'Choose Transformation for %s'%name
            popup = DictChoiceEditorPopup(title=title, name=name, size=size, pos=(0,0), cb=cbimg, keyname = getattr(self.target, keyname))
            from effects import effects
            popup.load_items(effects)
            popup.load_choices(self.target.effects)
            popup.open()
        t.bind(on_press=button_callback)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t

class StyleEditor(Editor):
    def getWidgets(self, name, keyname, **kwargs):
        t=Button(text="Define")
        def cbimg(value):
            try:
                #print 'attr', self.target, keyname, value, type(value)
                setattr(self.target, keyname, value)
                t.stored_value = value
            except ValueError,E:
                from conf import log
                log(E)
        t.bind(text=cbimg)
        def button_callback(instance):
            from kivy.core.window import Window
            cp_width = min(Window.size)
            size = Vector(Window.size)*.9
            title = 'Choose Styles for %s'%name
            popup = DictChoiceEditorPopup(title=title, name=name, size=size, pos=(0,0), cb=cbimg, keyname = getattr(self.target, keyname))
            from styles import styleList
            popup.load_items(styleList)
            popup.load_choices(self.target.styles)
            popup.open()
        t.bind(on_press=button_callback)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t

class FieldEditor(ChoiceEditor):
    "List all widgets fields from my parents"
    def getWidgets(self, name, keyname, **kwargs):
        from kivy.uix.spinner import Spinner
        from fields import Field
        fields = {x.name or x.Type: x for x in self.target.parent.children if isinstance(x, Field)}
        text = ""
        val = getattr(self.target,keyname)
        if val:
            text = val.name or val.Type
        t=Spinner(values=fields, text=text)
        def cb(instance,value):
            try:
                setattr(self.target, keyname, fields[value])
                t.stored_value = fields[value]
            except ValueError,E:
                from conf import log
                log(E)
        t.bind(text=cb)
        t.target_key = keyname
        t.stored_value = None
        t.target_attr = name
        return t


###############################################
#        POPUP                                #
###############################################

class FontEditorPopup(Popup):
    name = StringProperty()
    text = StringProperty()
    choices = ListProperty()
    italic = BooleanProperty()
    bold = BooleanProperty()
    font_name = StringProperty()
    font_size = NumericProperty()
    cb = ObjectProperty()

class FileEditorPopup(Popup):
    name = StringProperty()
    cb = ObjectProperty()
    path = StringProperty(".")
    filters = ListProperty()

class ColorEditorPopup(Popup):
    name = StringProperty()
    color = ObjectProperty()
    cb = ObjectProperty()

from kivy.uix.treeview import TreeView

class SubmitTreeView(TreeView):
    target= ObjectProperty()

    def on_touch_down(self, touch):
        if touch.is_double_tap:
            self.target.add_item()
        return super(SubmitTreeView, self).on_touch_down(touch)

class DictChoiceEditorPopup(Popup):
    name = StringProperty()
    cb = ObjectProperty()
    items = DictProperty()

    def load_items(self, items):
        self.items = items.copy()
        tree = self.ids.chooser
        from kivy.uix.treeview import TreeViewLabel
        for key in sorted(self.items):
            tree.add_node(TreeViewLabel(text=key))

    def load_choices(self, choices):
        from kivy.uix.label import Label
        from kivy.uix.checkbox import CheckBox
        picker = self.ids.picker
        # choice item are item from self.item dict. convert this to key, to find string
        keys = []
        values = []
        for k,v in self.items.items():
            keys.append(k)
            values.append(v)
        for c in choices:
            name = keys[values.index(c)]
            picker.add_widget(CheckBox(size_hint=(.2,None), height= 30))
            picker.add_widget(Label(text=name, size_hint=(.2, None), height=30))

    def add_item(self):
        from kivy.uix.label import Label
        from kivy.uix.checkbox import CheckBox
        selection = self.ids.chooser.selected_node
        picker = self.ids.picker
        if selection:
            name = selection.text
            picker.add_widget(CheckBox(size_hint=(.2,None), height= 30))
            picker.add_widget(Label(text=name, size_hint=(.2, None), height=30))

    def remove_item(self):
        grid = self.ids.picker
        cs = list(reversed(grid.children[:]))
        to_remove = list()
        for i in reversed(range((len(grid.children)-2)/2)):
            cb = cs[i*2+2]
            if cb.active:
                to_remove.extend(cs[i*2+2:i*2+4])
        for elt in to_remove:
            grid.remove_widget(elt)

    def compute(self):
        choices = list()
        grid = self.ids.picker
        cs = list(reversed(grid.children[:]))
        for i in reversed(range((len(grid.children)-2)/2)):
            name = cs[i*2+3].text
            choices.append(name)
        self.cb([self.items[x] for x in choices])

class ImageChoiceEditorPopup(Popup):
    name = StringProperty()
    cb = ObjectProperty()
    choices = DictProperty()

    def load_choices(self, choices):
        from kivy.uix.textinput import TextInput
        from kivy.uix.image import Image
        from kivy.uix.checkbox import CheckBox
        for name, path in choices.items():
            self.ids.imgpicker.add_widget(CheckBox(size_hint=(.2,None), height= 30))
            self.ids.imgpicker.add_widget(TextInput(text=name, size_hint=(.2, None), height=30))
            self.ids.imgpicker.add_widget(TextInput(text=path, size_hint=(.3, None), height=30))
            self.ids.imgpicker.add_widget(Image(source=path, size_hint=(.3, None), height=30))

    def add_image(self):
        from os.path import split, splitext
        from kivy.uix.textinput import TextInput
        from kivy.uix.image import Image
        from kivy.uix.checkbox import CheckBox
        from kivy.uix.boxlayout import BoxLayout
        selection = self.ids.imgchooser.selection
        if selection:
            path = selection[0]
            fname = split(path)[-1]
            name = splitext(fname)[0]
            self.ids.imgpicker.add_widget(CheckBox(size_hint=(.2,None), height= 30))
            self.ids.imgpicker.add_widget(TextInput(text=name, size_hint=(.2, None), height=30))
            self.ids.imgpicker.add_widget(TextInput(text=path, size_hint=(.3, None), height=30))
            self.ids.imgpicker.add_widget(Image(source=path, size_hint=(.3, None), height=30))

    def remove_image(self):
        grid = self.ids.imgpicker
        cs = list(reversed(grid.children[:]))
        to_remove = list()
        for i in reversed(range((len(grid.children)-4)/4)):
            cb = cs[i*4+4]
            if cb.active:
                print cs[i*4+4:i*4+8]
                to_remove.extend(cs[i*4+4:i*4+8])
        for elt in to_remove:
            grid.remove_widget(elt)

    def compute(self):
        self.choices = dict()
        grid = self.ids.imgpicker
        cs = list(reversed(grid.children[:]))
        for i in reversed(range((len(grid.children)-4)/4)):
            name = cs[i*4+5].text
            path = cs[i*4+6].text
            self.choices[name] = path
        self.cb(self.choices)

class ColorChoiceEditorPopup(Popup):
    name = StringProperty()
    cb = ObjectProperty()
    choices = DictProperty()

    def load_choices(self, choices):
        from kivy.uix.textinput import TextInput
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, Rectangle
        from kivy.uix.checkbox import CheckBox
        for name, selection in choices.items():
            self.ids.colorpicker.add_widget(CheckBox(size_hint=(.2,None), height= 30))
            self.ids.colorpicker.add_widget(TextInput(text=name, size_hint=(.2, None), height=30))
            w = Widget(size_hint=(.3, None), height=30)
            with w.canvas:
                Color(*selection)
                w.Rectangle = Rectangle(size=w.size, pos =w.pos)
            w.colorlist = selection[:]
            def reRect(instance,*args):
                instance.Rectangle.size = instance.size
                instance.Rectangle.pos = instance.pos
            w.bind(size=reRect, pos= reRect)
            self.ids.colorpicker.add_widget(w)

    def remove_color(self):
        grid = self.ids.colorpicker
        cs = list(reversed(grid.children[:]))
        to_remove = list()
        for i in reversed(range((len(grid.children)-4)/4)):
            cb = cs[i*4+4]
            if cb.active:
                print cs[i*4+4:i*4+8]
                to_remove.extend(cs[i*4+4:i*4+8])
        for elt in to_remove:
            grid.remove_widget(elt)

    def add_color(self):
        from kivy.uix.textinput import TextInput
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, Rectangle
        from kivy.uix.checkbox import CheckBox
        selection = self.ids.colorchooser.color
        name = self.ids.colorchooser.hex_color
        self.ids.colorpicker.add_widget(CheckBox(size_hint=(.2,None), height= 30))
        self.ids.colorpicker.add_widget(TextInput(text=name, size_hint=(.2, None), height=30))
        w = Widget(size_hint=(.3, None), height=30)
        with w.canvas:
            Color(*selection)
            w.Rectangle = Rectangle(size=w.size, pos =w.pos)
        w.colorlist = selection[:]
        def reRect(instance,*args):
            instance.Rectangle.size = instance.size
            instance.Rectangle.pos = instance.pos
        w.bind(size=reRect, pos= reRect)
        self.ids.colorpicker.add_widget(w)

    def compute(self):
        grid = self.ids.colorpicker
        cs = list(reversed(grid.children[:]))
        for i in reversed(range((len(grid.children)-3)/3)):
            txt = cs[3*i+1+3].text
            color = cs[3*i+2+3].colorlist
            self.choices[txt] = color
        self.cb(self.choices)

class SubImageEditorPopup(Popup):
    name = StringProperty()
    dimension = ListProperty(['',0,0,1,1])
    path = StringProperty()
    cb = ObjectProperty()


    def update_values(self, *args):
        #print 'update values called', args, self.ids.fpicker.selection
        if self.ids.fpicker.selection:
            path = self.ids.fpicker.selection[0]
        else:
            path = self.ids.img.source
        if not path:
            return
        overlay = self.ids.overlay
        #remove init pos from overlay.pos
        img = self.ids.img
        img_original_size = Vector(img.height * img.image_ratio, img.height)
        if img.height>img.width:
            img_original_pos = Vector(img.x + (img.width - img_original_size[0])/2 , img.y)
        else:
            img_original_pos = Vector(img.x, img.y+(img.height - img_original_size[1])/2)
        if img.image_ratio and img.height:
            self.ids.img_width.text = "%.2f"%(overlay.width/(img.height*img.image_ratio))
            self.ids.img_height.text = "%.2f"%(overlay.height/img.height)
            self.ids.img_x.text = "%.2f"%((overlay.x - 2.5*img_original_pos[0])/(img.height*img.image_ratio))
            self.ids.img_y.text = "%.2f"%((overlay.y - img_original_pos[1])/img.height)

editors_map = {
     NumericProperty: FloatEditor,
     StringProperty: TextEditor,
     OptionProperty: ChoiceEditor,
     ListProperty: ListEditor,
     BooleanProperty: BooleanEditor,
     float: FloatEditor,
     int: IntEditor,
     str: TextEditor,
     list: ListEditor,
     tuple: ListEditor,
}