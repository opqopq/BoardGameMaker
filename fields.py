"Contains all the diffrents fields for template"

from collections import OrderedDict

from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics.texture import Texture
from PIL import Image as PILImage

from utils.hoverable import HoverBehavior
from img_xfos import img_modes

#Fbo
from kivy.graphics import Color, Rectangle, Canvas
from kivy.graphics.fbo import Fbo
from utils.symbol_label import SymbolLabel
from kivy.uix.effectwidget import EffectWidget


Builder.load_file('kv/fields.kv')

from editors import *

#Pre-import styles to register them all
from styles import getStyle

###############################################
#        Field                                #
###############################################

class BaseField(FloatLayout):
    pass

class OBaseField(FloatLayout):

    inner_texture = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.canvas = Canvas()
        with self.canvas:
            self.fbo = Fbo(size=self.size)
            Color(1, 1, 1)
            self.fbo_rect = Rectangle()

        # wait that all the instructions are in the canvas to set texture
        self.inner_texture = self.fbo.texture
        super(BaseField, self).__init__(**kwargs)

    def add_widget(self, *largs):
        # trick to attach graphics instructino to fbo instead of canvas
        canvas = self.canvas
        self.canvas = self.fbo
        ret = super(BaseField, self).add_widget(*largs)
        self.canvas = canvas
        return ret

    def remove_widget(self, *largs):
        canvas = self.canvas
        self.canvas = self.fbo
        super(BaseField, self).remove_widget(*largs)
        self.canvas = canvas

    def on_size(self, instance, value):
        value = [int(round(x)) for x in self.size]
        self.fbo.size = value
        self.inner_texture = self.fbo.texture
        self.fbo_rect.size = value

    def on_pos(self, instance, value):
        value = [int(round(x)) for x in self.pos]
        self.fbo_rect.pos = value

    def on_inner_exture(self, instance, value):
        self.fbo_rect.texture = value

class Field(FloatLayout, HoverBehavior):
    "Element class represent any component of a template (fields, font, transformation....)"
    selected = BooleanProperty(False)
    z = NumericProperty(0)
    # Shown is false when we don't want the template params to be showed in the deck panel
    editable = BooleanProperty(True)
    # True if we are in designer mode. If yes, I'm movable/scalable & rotatable
    designed = BooleanProperty(False)

    #angle of rotation, centered on my center
    angle = NumericProperty(0)
    bg_color= ListProperty([0,0,0,0])
    name = StringProperty()
    #Attributes that are only used in designed mode
    attrs=OrderedDict([
            ("name",TextEditor), ('x', MetricEditor), ('y', MetricEditor), ('z', AdvancedIntEditor), ('width', MetricEditor),('height',MetricEditor),
            ('opacity', AdvancedRangeEditor), ('angle',AdvancedIntEditor), ('bg_color',ColorEditor),('editable', BooleanEditor), ('default_attr', ChoiceEditor), ("styles", StyleEditor)
    ])
    #Default Attr is the name of the attribute that souhld be editable in the deck editor (vs all in designer). Several one, if a list
    default_attr = ""
    #List of attr name for this class that should not be exported from designer
    not_exported = ['cls', 'width','height','parent','designed','children','selected','right','border_point','hovered', 'top','center','center_x','center_y','x','y', 'texture', 'texture_size', 'Type']

    #This one are used for easier display of the template as a widget
    #In KV File, just add some entry into vars (attrName, Editor) to have the desired entry in Deck Widget Tree
    vars = DictProperty()

    #Styles: dynaic list of appliyed style. .KLass kv file rules
    styles = ListProperty()

    #Black list: as params, this set aggregats the not_exported info from base classes
    black_list = set(not_exported)

    #Menu is an ordered dict  listing which attributes needs to be in which sub tree for editors
    #_menu work for current instance
    # menu aggregate parent info
    _menu = OrderedDict([('Object',['name','editable','default_attr']),("Shape",['x','y','z','width','height','opacity','angle','bg_color'])])

    Type = 'Field'

    def on_styles(self, instance, styles):
        before = set(self.cls)
        now = set([x.lower() for x in styles])
        new = now-before
        rules = [x for x in Builder.rules if x[0].key in new]
        rsnames = [x[0].key for x in Builder.rules]
        for rule in rules:
            try:
                Builder._apply_rule(self, rule[1], rule[1])
            except Exception,E:
                print E
        #Now that rules have been appliyed singularly, change my cls, for the future
        self.cls = [x.lower() for x in styles]
        #do not do full apply through Builder.apply(self): this will trigger full consumption

    def on_designed(self,instance, designed):
        if designed:
            drule = [x for x in Builder.rules if x[0].key == 'designed'][0][1]
            Builder._apply_rule(self, drule, drule)

    def prepare_export(self):
        "Use to create a subclassable list of not exported field"
        self.black_list = set()
        import inspect
        for klass in reversed(inspect.getmro(self.__class__)):
            if klass == object:
                continue
            if not hasattr(klass, 'not_exported'):
                continue
            for k in klass.not_exported:
                self.black_list.add(k)

    def __init__(self, **kwargs):
        "Create a subclassable list of attributes to display"
        super(Field, self).__init__(**kwargs)
        self.derive_infos()

    def derive_infos(self):
        #Compute menu & params
        import inspect
        self.params = OrderedDict()
        self.menu = OrderedDict()
        for klass in reversed(inspect.getmro(self.__class__)):
            if not issubclass(klass, Field):
                continue
            for k,v in klass.attrs.items():
                self.params[k] = v
            for k,v in klass._menu.items():
                self.menu[k] = v
        self.default_attr_values = self.params.keys()

    def __repr__(self):
        return '<%s-%s>'%(self.Type,  self.id or self.name)

    def getChangedAttributes(self,restrict):
        blank = self.__class__()
        res = self.getDelta(blank)
        if restrict:#remove duplicate entr like pos/x/y or size/width/height
            res.difference_update(self.black_list)
        return res

    def getDelta(self, other):
        if other.__class__ != self.__class__:
            raise TypeError('Can only compare same class. Received %s compared to %s'%(other.__class, self.__class__))
        results = set()
        for attrName in dir(self.__class__):
            attr = getattr(self.__class__, attrName)
            #Remove non attribute stuff
            if not isinstance(attr, (Property, dict, list, int, float, tuple, basestring)):
                continue
            try:
                instance = getattr(self, attrName)
                binstance = getattr(other, attrName)
                if binstance != instance:
                    results.add(attrName)
            except KeyError, E:
                import traceback
                print 'While GetDelta between %s and %s: Issue with key %s. Maybe due to styles: %s'%(self,other, attrName, self.styles)
        return results

    def Copy(self):
        blank = self.__class__()
        for attr in self.getChangedAttributes(False):
            setattr(blank, attr, getattr(self,attr))
        blank.parent = None
        blank.name = (self.name or self.Type ) +'-copy'
        return blank

    def getEditor(self, name, add_label=False, **kwargs):
        #Return the widget used in the template params list for editing fieldvalue in deck mode
        #print 'creating editors for', self
        box_klass = Factory.get('BoxLayout')
        box = box_klass()
        if len(self.params)==1:
            fname = self.params.keys()[0]
            print 'adding single box for',name
            box.orientation="horizontal"
            box.size_hint = 1,None
            box.height = 30
            box.add_widget(Label(text=name, size_hint=(None,None), height=30))
            editor = self.params[fname](self)
            editor.create(name, fname, **kwargs)
            box.add_widget(editor.widget)
        else:
            box.orientation="vertical"
            box.size_hint = 1,None
            box.height = 80

            box.add_widget(Label(text="--%s--"%name,size_hint=(1,None), height=20))
            for fname in self.params:
                print '\tadding box for',fname , ' of', name
                b = box_klass(orientation='horizontal', size_hint=(1,None), height=30)
                if add_label:
                    b.add_widget(Label(text=name, size_hint=(None,None), height=30))
                b.add_widget(Label(text=fname, size_hint=(None,None), height=30))
                editor = self.params[fname](self)
                editor.create(name, fname, **kwargs)
                b.add_widget(editor.widget)
                box.add_widget(b)
        return box

    def on_touch_down(self, touch):
        if self.designed:
            origin = Vector(*touch.pos)
            for pos in [(self.center_x,self.y+5), (self.center_x, self.top-5),(self.x+5, self.center_y),(self.right-5,self.center_y),(self.right-5, self.top-5),(self.x+5,self.y+5),(self.x+5,self.top-5),(self.right-5,self.y+5)]:
                if self.selected and origin.distance(Vector(*pos)) <5:
                    touch.ud['do_resize'] = True
                    touch.grab(self)
                    #Calculate the mode of resizing
                    ox,oy = touch.opos
                    cx,cy = self.center
                    touch.ud['LEFT'] = ox<cx
                    touch.ud['DOWN'] = oy<cy
                    if pos in [(self.center_x,self.y+5), (self.center_x, self.top-5)]:
                        touch.ud['movement'] = 'y'
                    if pos in [(self.x+5, self.center_y), (self.right-5,self.center_y)]:
                        touch.ud['movement'] = 'x'
                    if pos in [(self.x+5,self.y+5),(self.x+5,self.top-5),(self.right-5, self.top-5), (self.right-5,self.y+5)]:
                        touch.ud['movement']= 'xy'
                    return True
            if self.collide_point(*touch.pos):
                touch.grab(self)
                #Define if resized is on
                touch.ud['do_resize'] = False
                #Here I should watch if shift is set, then it would be an append.
                self.selected = True
                #why parent.parent: because ruled scatter is a scatterlayout: floatlayout + scatter (2 levels)
                if self.designer.selection and self.designer.selection[0] is not self:
                    self.designer.selection[0].selected = False
                self.designer.selection = [self]
                return True
            else:
                self.selected = False
                self.designer.selection = list()
        return super(Field, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.designed  and touch.grab_current==self:
            touch.ungrab(self)
        return super(Field, self).on_touch_up(touch)

    def on_touch_move(self, touch):
        if self.designed and touch.grab_current==self:
            if touch.ud['do_resize']: #Resize
                LEFT = touch.ud['LEFT']
                DOWN = touch.ud['DOWN']
                MOV_X = 'x' in touch.ud['movement']
                MOV_Y = 'y' in touch.ud['movement']
                if MOV_Y:
                    if DOWN:
                        self.y += touch.dy
                        self.height -= touch.dy
                    else:
                        self.height += touch.dy
                if MOV_X:
                    if LEFT:
                        self.x += touch.dx
                        self.width -= touch.dx
                    else:
                        self.width += touch.dx
            else:#Move
                self.x += touch.dx
                self.y += touch.dy
        return super(Field, self).on_touch_move(touch)

    def on_z(self, instance, value):
        #Resort all dad'children
        if self.parent:
            cs = self.parent.children[:]
            cs.sort(key=lambda x: x.z, reverse=True)
            self.parent.children= cs
            #Also reorder canvas
            for c in cs:
                self.parent.canvas.remove(c.canvas)
                self.parent.canvas.insert(0,c.canvas)

    def add_widget(self, widget, index=0):
        #replacing index by z-index
        super(FloatLayout, self).add_widget(widget, getattr(widget,'z',0))
        #Re order them according to z elt:
        cs = self.children[:]
        cs.sort(key= lambda x: getattr(x,'z',0), reverse=True)
        self.children = cs
        #Also reorder canvas
        for cindex, c in enumerate(self.children):
            self.canvas.remove(c.canvas)
            self.canvas.insert(0,c.canvas)

    def remove_widget(self, widget):
        super(FloatLayout,self).remove_widget(widget)
        cs = self.children[:]
        cs.sort(key= lambda x: getattr(x,'z',0), reverse=True)
        self.children = cs
        #Also reorder canvas
        for cindex, c in enumerate(self.children):
            self.canvas.remove(c.canvas)
            self.canvas.insert(0,c.canvas)


class TextField(Label, Field):
    autofit = BooleanProperty(False)
    max_font_size = NumericProperty()
    min_font_size = NumericProperty()
    halign_values = ['left','center','right','justify']
    valign_values = ['bottom','middle','top']
    attrs = OrderedDict([
        ('text', TextEditor), ('autofit', BooleanEditor),
        ('max_font_size', IntEditor), ('min_font_size', IntEditor),
        ('color', ColorEditor),
        ('halign',ChoiceEditor), ('valign', ChoiceEditor),
        ('font', FontChoiceEditor) ])
    # ('font_size', IntEditor), ('font_name', FontChoiceEditor), ('bold', BooleanEditor),  ('italic', BooleanEditor)])
    static_font_size = NumericProperty()
    default_attr = "text"

    not_exported = ['static_font_size', 'font', 'text_size']
    font = ListProperty(['DroidSans.ttf', 8,False, False])

    def on_size(self,instance, size):
        self.text_size = size
        self.on_text(instance,self.text)

    def on_autofit(self, instance, autofit):
        if autofit:
            #store the format static value
            self.static_font_size = self.font_size
            #Now calculate the new one
        else:
            #Restore former size, if it exists
            if self.static_font_size:
                self.font_size = self.static_font_size
        self.on_text(instance, None)

    def on_text(self, base, *args):
        if self.autofit:
            if not self.text:
                return
            #Auto fit to shrink
            changed = False
            # while self.texture_size> self.size:
            while self._label.get_extents(self.text)[0]>= self.width or self._label.get_extents(self.text)[1]>=self.height:
                if self.min_font_size and self.font_size<=self.min_font_size:
                    break
                self.font_size-=1
                changed = True
            if changed:
                #No need to test for grownth:
                return
            #Auto fit to growth
            while self._label.get_extents(self.text)[0]<= self.width and self._label.get_extents(self.text)[1]<= self.height:
                if self.max_font_size and self.font_size>=self.max_font_size:
                    break
                self.font_size+=1

class ImageField(Image, Field):
    mask = StringProperty()
    attrs = OrderedDict([('source', FileEditor), ('allow_stretch', BooleanEditor), ('keep_ratio', BooleanEditor), ('mask', FileEditor)])
    not_exported = ['image_ratio', 'texture', 'norm_image_size', 'scale', 'texture_size']
    default_attr = 'source'
    source_filters = ['*.jpg','*.gif','*.jpeg','*.bmp','*.png']

    def on_source(self, instance, source):
        from os.path import isfile
        if not isfile(source):
            from conf import log
            log('Source does not exist for ImageField %s: %s'%(self.name, source))

class ColorField(Field):
    "Display a color on a rectangle"
    rgba=ListProperty((1,1,1,1))
    attrs={'rgba': ColorEditor}
    default_attr = 'rgba'

class BorderField(Field):
    "Draw 4 lines around parent"
    border_width=NumericProperty(1)
    border_color=ListProperty((1,1,1,1))
    attrs={'border_width': BorderEditor , 'border_color': ColorEditor}
    default_attr = 'border_color'

class ImgChoiceField(Image, Field):
    "This widget will display an image base on a choice, helds in choices dict"
    choices = DictProperty()
    attrs = OrderedDict([('selection',ImgOptionEditor),('choices', ImageChoiceEditor),('allow_stretch', BooleanEditor), ('keep_ratio', BooleanEditor)])
    default_attr = 'selection'
    not_exported = ['image_ratio','texture', 'norm_image_size', 'scale','selection_values','source']
    selection = StringProperty()
    selection_values= ListProperty()

    def on_selection(self, instance, selection):
        if self.choices:
            self.source = self.choices[selection]

    def on_choices(self, instance, choices):
        self.selection_values = choices.keys()
        if choices and not self.selection:
            self.selection = choices.keys()[0]
        else:
            #force selection
            self.on_selection(self, self.selection)

class ColorChoiceField(Field):
    "This widget will display an image base on a choice, helds in choices dict"
    choices = DictProperty()
    attrs = OrderedDict([('selection', ColorOptionEditor),('choices', ColorChoiceEditor)])
    default_attr = 'selection'
    not_exported = ['selection_values', 'rgba']
    selection = StringProperty()
    selection_values = ListProperty()
    rgba=ListProperty((1,1,1,1))

    def on_selection(self, instance, selection):
        if self.choices:
            self.rgba = self.choices[selection]

    def on_choices(self, instance, choices):
        self.selection_values = choices.keys()
        if choices and not self.selection:
            self.selection = choices.keys()[0]
        else:
            self.on_selection(instance, self.selection)

class SymbolField(SymbolLabel, Field):
    source=StringProperty()
    default_attr = 'text'

    def __init__(self,**kwargs):
        SymbolLabel.__init__(self,**kwargs)
        #Auto read any symbol file that would tell me what to do

    def _postProcess(self):
        "Post Processing: auto load data file"
        from json import load
        import os.path
        if self.source:

            if os.path.isfile(self.source):
                #print "Loading source provided file"
                self.symbol_dict=load(file(self.source,'rb'))
        else:
            if  hasattr(self,'symbol_dict') and self.symbol_dict:
                #Auto load any json file save with my id
                #print  os.path.isfile('%s_source.json'%self._name)
                if hasattr(self,'_name') and os.path.isfile('%s_source.json'%self._name):
                    #print "Auto loading symbol file"
                    self.symbol_dict=load(file('%s_source.json'%self._name,'rb'))

    def GetValueWidgets(self,name):
        ws=list()
        ws.append(Label(text=name))
        t=Button(text='Edit')
        #Create a callback for the modal frame
        def cb(instance):
            self.text=instance.content.text
        #Create callback for button that would start a modal
        def button_callback(instance):
            from kivy.core.window import Window
            cp_width = min(Window.size)*.5
            cp_pos = [(Window.size[0]-cp_width)/2,(Window.size[1]-cp_width)/2]
            popup = Popup(title='Edit Content for %s'%name, content=TextInput(text=self.text,multiline=True),auto_dismiss=True,pos = cp_pos, size=(cp_width,cp_width), size_hint=(None,None))
            popup.bind(on_dismiss=cb)
            popup.open()
        #Assign it
        t.bind(on_press=button_callback)
        ws.append(t)
        return ws

class SubImageField(Field):
    default_attr = 'dimension'
    attrs = {"dimension": SubImageEditor}
    #Dimension is: source, x, y, width, height
    dimension = ListProperty(["", 0, 0, 1, 1])
    texture = ObjectProperty(None)
    not_exported = ['texture']

    def on_dimension(self, instance, dimension):
        from kivy.core.image import Image
        IMG = Image(dimension[0]).texture
        width, height = IMG.width, IMG.height
        self.texture = Image(dimension[0]).texture.get_region(self.dimension[1]*width,self.dimension[2]*height, self.dimension[3]*width,self.dimension[4]*height)

class TransfoField(Field):
    "Transform an image file thourgh different methods registered in img_xfos.py"
    default_attr = 'source'
    not_exported = ['texture', 'Image']
    attrs = {'source': FileEditor, 'xfos': TransfoListEditor}

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

class SvgField(Field):
    source = StringProperty()
    source_filters = ['*.svg']
    attrs = {'source': FileEditor}
    default_attr = 'source'

    def on_source(self,instance, source):
        from os.path import isfile
        if isfile(source):
            with self.canvas:
                from kivy.graphics.svg import Svg
                Svg(source)
        else:
            from conf import log

            try:
                log('Not exsting SVG source: %s'%source)
            except AttributeError:
                #This if svg error occurs before the loger exists
                print 'Not existing SVG source:%s'%source

class ShapeField(Field):
    dash_length = NumericProperty()
    dash_offset = NumericProperty()
    line_width = NumericProperty(1)
    line_color = ListProperty([1,1,1,1])
    cap = StringProperty('round')
    cap_values = ['round','none','square']
    joint = StringProperty('round')
    joint_values = ["none", "miter", "bevel",'round']
    default_attr = 'line_width'
    attrs = OrderedDict([
                        ('dash_length', AdvancedIntEditor),
                        ('dash_offset', AdvancedIntEditor),
                        ('line_width', AdvancedIntEditor),
                        ('line_color', ColorEditor),
                        ('cap',ChoiceEditor),
                        ('joint', ChoiceEditor)
                        ])
    not_exported = ['joint_values','cap_values']

    _menu = {'Line':attrs.keys()}

class LineField(ShapeField):
    #Just goigng from lower left to upper right. is it even useful ?
    pass

class CircleField(ShapeField):
    angle_start = NumericProperty(0)
    angle_end = NumericProperty(360)
    attrs = OrderedDict([('angle_start', AdvancedIntEditor), ('angle_end', AdvancedIntEditor)])

class RectangleField(ShapeField):
    corner_radius = NumericProperty(0)
    default_attr = 'corner_radius'
    attrs = {'corner_radius': AdvancedIntEditor}

class SourceShapeField(ShapeField):
    skip_designer = True
    source = StringProperty(None)
    source_filters = ('*.png', '*.jpg', '*.jpeg', '*.gif')
    texture = ObjectProperty(None, allownone=True)
    attrs = {'source': FileEditor}
    default_attr = 'source'

class EllipseField(SourceShapeField):
    skip_designer = False
    angle_start = NumericProperty(0)
    angle_end = NumericProperty(360)
    attrs = OrderedDict([('angle_start', AdvancedIntEditor), ('angle_end', AdvancedIntEditor)])

class FilledRectangleField(SourceShapeField):
    skip_designer = False

class PolygonField(SourceShapeField):
    skip_designer = False
    attrs = {'side': AdvancedIntEditor, 'angle_start': AdvancedIntEditor}
    side = NumericProperty(4)
    angle_start = NumericProperty(0)
    vertices = ListProperty()

    not_exported = ['vertices']

    def on_pos(self, instance,pos):
        if hasattr(ShapeField, 'on_pos'):
            super(PolygonField, self).on_pos(instance, pos)
        self.on_side(instance, self.side)

    def on_size(self, instance, size):
        if hasattr(ShapeField, 'on_size'):
            ShapeField.on_size(self, instance, size)
        self.on_side(instance, self.side)

    def on_angle_start(self, instance, angle):
        self.on_side(instance, self.side)

    def on_side(self, instance, side):
        from math import cos, sin, pi, radians
        cx, cy = self.center
        a = 2 * pi / side
        self.vertices = []
        for i in xrange(side):
            self.vertices.extend([
                cx + cos(radians(self.angle_start) + i * a) * float(self.width)/2,
                cy + sin(radians(self.angle_start) + i * a) * float(self.height)/2,
                .5+ 0.5*cos(radians(self.angle_start) + i * a), #cos(radians(self.angle_start) + i * a),
                .5-.5*sin(radians(self.angle_start) + i * a),#sin(radians(self.angle_start) + i * a)
            ])

class LinkedField(Field):
    "Abstrat class usedd to point out field that have children"

class CopyField(LinkedField):
    target = ObjectProperty()
    skip_list = ListProperty(['name'])
    default_attr = 'target'
    attrs = {'target': FieldEditor}
    # No type: will be overidden by target
    not_exported = ['target', 'skip_list']

    def callback_setter(self, src, dst, attr):
        def inner(instance, value):
            #print 'forwarding %s (%s) from %s to %s / %s' % (attr,value, src, instance, dst)
            setattr(dst, attr, value)
        return inner

    def on_target(self, instance, target):
        blank = target.__class__()
        self.add_widget(blank)
        # First, bind all params from target to blank
        for attr in target.params:
            if not attr in target.properties():
                continue
            kw = {attr: self.callback_setter(attr=attr, src=target, dst= blank)}
            try:
                target.unbind(**kw)
            except KeyError: # binding does not exists
                pass
            if attr in self.skip_list:
                continue
            # Copy value
            try:
                setattr(blank, attr, getattr(target, attr))
            except Exception, E:
                import traceback
                print 'Error while duplicating ', blank, attr, getattr(target,attr), ' Exception raised:',E
                traceback.print_exc()
            target.bind(**kw)
        # Then bind all params from ME to blank
        for attr in self.params:
            if attr in ('target', 'parent', 'skip_list', 'default_attr', 'attrs'):
                continue
            if attr not in target.properties():
                continue
            kw = {attr: self.callback_setter(attr=attr, src=self, dst=blank)}
            try:
                self.unbind(**kw)
            except KeyError:  # binding does not exists
                pass
            # Copy value
            try:
                setattr(blank, attr, getattr(self, attr))
            except Exception, E:
                import traceback
                print 'Error while conveying', blank, attr, getattr(self,attr), ' Exception raised:',E
                from conf import log
                log(E, traceback.format_exc())
            self.bind(**kw)

class EffectField(EffectWidget, LinkedField):
    attrs = {'effects': EffectsEditor}
    default_attr = 'effects'

# Special case used only for SubImageEditor
class OverlayField(RectangleField):
    skip_designer = True

    def on_touch_down(self, touch):
        if self.designed:
            origin = Vector(*touch.pos)
            for pos in [(self.center_x,self.y+5), (self.center_x, self.right-5),(self.x+5, self.center_y),(self.right-5,self.center_y),(self.right-5, self.top-5),(self.x+5,self.y+5),(self.x+5,self.top-5),(self.right-5,self.y+5)]:
                if self.selected and origin.distance(Vector(*pos)) <5:
                    touch.ud['do_resize'] = True
                    touch.grab(self)
                    #Calculate the mode of resizing
                    ox, oy = touch.opos
                    cx, cy = self.center
                    touch.ud['LEFT'] = ox<cx
                    touch.ud['DOWN'] = oy<cy
                    return True
            if self.collide_point(*touch.pos):
                touch.grab(self)
                #Define if resized is on
                touch.ud['do_resize'] = False
                #Here I should watch if shift is set, then it would be an append.
                return True
        return super(Field, self).on_touch_down(touch)

###############################################
#        Misc                                 #
###############################################

fieldDict = dict()

for klassName in globals().keys()[:]:
    klass = globals()[klassName]
    if type(klass) == type(Field) and issubclass(klass, Field):
        #Remove the shape from this list
        if klass is Field:
            continue
        klass.Type = klassName
        fieldDict[klass.Type] = klass