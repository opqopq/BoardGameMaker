"""Contains all the diffrents fields for template"""

from collections import OrderedDict
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.factory import Factory
from kivy.properties import ObservableDict, ObservableList, ObservableReferenceList
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics.texture import Texture
from PIL import Image as PILImage
from kivy.uix.behaviors import FocusBehavior
from utils.hoverable import HoverBehavior
from kivy.graphics import Color, Rectangle, Canvas
from kivy.graphics.fbo import Fbo
from utils.symbol_label import SymbolLabel
from kivy.uix.effectwidget import EffectWidget
from editors import *
from conf import gamepath, find_path
from os.path import relpath


Builder.load_file('kv/fields.kv')


# Pre-import styles to register them all
from styles import getStyle

###############################################
#        Field                                #
###############################################

from kivy.graphics import ClearBuffers, ClearColor

def compare_to_root(rootsize,fieldsize):
    "Take 2 size or pos tuple and return a string made of b/a ratio as string, rounded to 2 digits float"
    xa, ya = rootsize
    xb, yb = fieldsize
    assert xa and ya
    xratio = float(xb)/float(xa)
    yratio = float(yb)/float(ya)
    rounded_x = round(xratio,2)
    rounded_y = round(yratio,2)
    if rounded_y == 1:
        str_y = 'root.height'
    else:
        str_y = '%.2f * root.height' % rounded_y
    if rounded_x== 1:
        str_x = 'root.width'
    else:
        str_x = '%.2f * root.width' % rounded_x
    return "%s, %s" % (str_x, str_y)

class BaseField(HoverBehavior, FocusBehavior):
    """Element class represent any component of a template (fields, font, transformation....)"""
    selected = BooleanProperty(False)
    z = NumericProperty(0)
    # Shown is false when we don't want the template params to be showed in the deck panel
    editable = BooleanProperty(True)
    # True if we are in designer mode. If yes, I'm movable/scalable & rotatable
    designed = BooleanProperty(False)

    #angle of rotation, centered on my center
    angle = NumericProperty(0)
    bg_color= ListProperty([0, 0, 0, 0])
    name = StringProperty()
    #Attributes that are only used in designed mode
    attrs=OrderedDict([
            ("name",TextEditor), ('x', MetricEditor), ('y', MetricEditor), ('z', AdvancedIntEditor), ('width', MetricEditor),('height',MetricEditor), ('size_hint', SizeHintEditor), ('pos_hint', PosHintEditor),
            ('opacity', AdvancedRangeEditor), ('angle',AdvancedIntEditor), ('bg_color',ColorEditor),('editable', BooleanEditor), ('default_attr', ChoiceEditor), ("styles", StyleEditor)
    ])
    #Default Attr is the name of the attribute that souhld be editable in the deck editor (vs all in designer). Several one, if a list
    default_attr = ""
    #List of attr name for this class that should not be exported from designer
    not_exported = ['template', "directives", "code_behind", 'sel_radius', 'cls', 'focus','focused', 'width','height','parent','designed','children','selected','right','border_point','hovered', 'top','center','center_x','center_y','x','y', 'texture', 'texture_size', 'Type', 'size_hint_x','size_hint_y']

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
    _menu = OrderedDict([('Object',['name','editable','default_attr']),("Shape",['x','y','z','width','height','size_hint', 'pos_hint','opacity','angle','bg_color'])])

    Type = 'Field'

    #place to hold all kv codes from designeer
    code_behind = DictProperty()

    #Includes all the directives, like import or set.
    directives = ListProperty()

    #Pointer to the template we are part of. easier for evaluating context of a template
    template = ObjectProperty()

    def on_focus(self,instance, focus):
        if self.designed and focus:
            self.selected = focus
        #if not focused anymore, it does not means that it is not current selection

    def on_selected(self, instance, selected):
        self.focused = selected

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if self.designed:
            code,text= keycode
            if text in ('left','right','up','down'):
                DIR = 'x'
                STEP = 1
                if 'ctrl' in modifiers or 'meta' in modifiers:
                    STEP *= 10
                if text == 'left':
                    STEP *= -1
                elif text == 'up':
                    DIR = 'y'
                elif text == 'down':
                    DIR = 'y'
                    STEP *=-1
                elif text =='right':
                    pass
                setattr(self, DIR, getattr(self, DIR) + STEP)
            if text in ('delete',):
                self.designer.remove_selection()

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

    def derive_infos(self):
        #Compute menu & params
        import inspect
        self.params = OrderedDict()
        self.menu = OrderedDict()
        self.code_behind = dict()
        for klass in reversed(inspect.getmro(self.__class__)):
            if not issubclass(klass, BaseField):
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
            if attrName == 'is_context':
                continue
            try:
                instance = getattr(self, attrName)
                binstance = getattr(other, attrName)
                if binstance != instance:
                    results.add(attrName)
                    #print 'diff', attrName, instance, binstance
            except (KeyError, AttributeError), E:
                import traceback
                print 'While GetDelta between %s and %s: Issue with key %s. Maybe due to styles: %s'%(self,other, attrName, self.styles)
        return results

    def Copy(self, with_children = False):
        blank = self.__class__()
        for attr in self.getChangedAttributes(True):
            try:
                setattr(blank, attr, getattr(self,attr))
            except AttributeError, E:
                print 'skipping attribute copying for ',attr, ':', E
        blank.parent = None
        blank.name = (self.name or self.Type ) +'-copy'
        if with_children:
            for child in self.children:
                if not isinstance(child, BaseField):
                    continue
                print 'copying child', child
                blank.add_widget(child.Copy(with_children))
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


    def export_field(self, level = 2, save_cm = True, relativ = True, save_relpath = True):
        from types import FunctionType
        from template import BGTemplate
        tmpls = list()
        imports = list()
        directives = list()
        prepend = '\t'*level
        field = self
        #If we have no connection to master template, what is the point of this comparison.
        if relativ and not self.template:
            relativ = False
        #Remove field from any not desired attrbiute for export
        field.prepare_export()
        tmpls.append('%s%s:'%((level-1)*'\t',field.Type))
        #Include KV file if templateField
        if isinstance(field, BGTemplate):
            tmpls[0] = '%s%s:'%((level-1)*'\t',field.template_name)
            imports.append(field.src.split('@')[-1])
        if field.directives:
            directives.extend(field.directives)
        for attr in field.getChangedAttributes(restrict=True):
            #Check if code behind:
            if attr in field.code_behind:
                #print 'Attr %s has been changed and should be written down. One could write the code behind:'%attr, field.code_behind[attr]
                tmpls.append('%s%s: %s'%(prepend, attr, field.code_behind[attr]))
                continue
            #convert name to ID
            value = getattr(field,attr)
            vtype = type(value)
            #print 'exporting field', attr, vtype
            if attr == 'name':
                tmpls.append('%sid: %s'%(prepend,value))
            elif  isinstance(value, basestring):
                if isfile(value) and save_relpath:
                    value = relpath(value, gamepath)
                tmpls.append('%s%s: "%s"'%(prepend,attr, value))
            elif vtype == type(1.0):
                tmpls.append('%s%s: %.2f'%(prepend, attr, value))
            elif vtype in  (type({}), ObservableDict):
                for _v in value:
                    try:
                        _uni = unicode(value[_v], 'latin-1')
                    except TypeError: #can not coerce float in latin -1
                        _uni = unicode(value[_v])
                    if isfile(_uni) and save_relpath:
                        value[_v] = relpath(value[_v], gamepath)
                tmpls.append('%s%s: %s'%(prepend, attr,value))
            elif vtype in (type(tuple()), type(list()), ObservableList, ObservableReferenceList):
                if attr in ("size","pos"):
                    if relativ:
                        tmpls.append('%s%s: %s'%(prepend, attr, compare_to_root(self.template.size,value)))
                        continue
                    if save_cm:
                        tmpls.append('%s%s: '%(prepend,attr)+', '.join(["cm(%.2f)"%(v/cm(1)) for v in value]))
                        continue
                #Looping and removing bracket
                sub = []
                for item in value:
                    if isinstance(item, float):
                        sub.append('%.2f'%item)
                    elif isinstance(item, basestring):
                        if isfile(item) and save_relpath:
                            item = relpath(item, gamepath)
                        sub.append('"%s"'%item)
                    elif isinstance(item, FunctionType): #replace the function by its name without the ""
                        sub.append('%s'%item.func_name)
                    else:
                        sub.append(str(item))
                if len(sub) != 1:
                    tmpls.append('%s%s: '%(prepend, attr) + ', '.join(sub))
                else: #only: add a ',' at the end, to have kv understand it is a tuple
                    tmpls.append('%s%s: '%(prepend, attr) + sub[0] + ',')

            else:
                tmpls.append('%s%s: %s'%(prepend, attr, value))
        if isinstance(field, LinkedField):
            for child in field.children:
                if getattr(child, 'is_context', False):
                    continue
                if not isinstance(child, BaseField):
                    continue
                t,i,d = child.export_field(level=level+1, relativ=relativ, save_cm = save_cm, save_relpath = save_relpath)
                tmpls.extend(t)
                imports.extend(i)
                directives.extend(d)
        tmpls.append('')
        return (tmpls, imports, directives)

#class Field(HoverBehavior, FocusBehavior, FloatLayout):
from kivy.uix.relativelayout import RelativeLayout
class Field( BaseField, RelativeLayout):

    def __init__(self, **kwargs):
        "Create a subclassable list of attributes to display"
        RelativeLayout.__init__(self,**kwargs)
        self.derive_infos()

    def on_touch_down(self, touch):
        if self.designed:
            origin = Vector(*touch.pos)
            #Convert origin to take into account self.angle
            for pos in [(self.center_x,self.y+self.sel_radius), (self.center_x, self.top-self.sel_radius),(self.x+self.sel_radius, self.center_y),(self.right-self.sel_radius,self.center_y),(self.right-self.sel_radius, self.top-self.sel_radius),(self.x+self.sel_radius,self.y+self.sel_radius),(self.x+self.sel_radius,self.top-self.sel_radius),(self.right-self.sel_radius,self.y+self.sel_radius)]:
                if self.selected:
                    VECTOR = Vector(*pos)
                    if self.angle:
                        deltapos = Vector(pos[0] - self.center[0], pos[1] - self.center[1])
                        deltapos =  deltapos.rotate(self.angle)
                        VECTOR = deltapos + self.center
                    if origin.distance(VECTOR) <5:
                        touch.ud['do_resize'] = True
                        touch.grab(self)
                        #Calculate the mode of resizing
                        ox,oy = touch.opos
                        cx,cy = self.center
                        touch.ud['LEFT'] = ox<cx
                        touch.ud['DOWN'] = oy<cy
                        if pos in [(self.center_x, self.y+self.sel_radius), (self.center_x, self.top-self.sel_radius)]:
                            touch.ud['movement'] = 'y'
                        if pos in [(self.x+self.sel_radius, self.center_y), (self.right-self.sel_radius, self.center_y)]:
                            touch.ud['movement'] = 'x'
                        if pos in [(self.x+self.sel_radius, self.y+self.sel_radius),(self.x+self.sel_radius, self.top-self.sel_radius), (self.right-self.sel_radius, self.top-self.sel_radius), (self.right-self.sel_radius, self.y+self.sel_radius)]:
                            touch.ud['movement'] = 'xy'
                        return True
            if self.collide_point(*touch.pos):
                touch.grab(self)
                #Define if resized is on
                touch.ud['do_resize'] = False
                #Display params if duoble tap
                if touch.is_double_tap:
                    self.designer.display_field_attributes(self)
                return True
            else:
                self.selected = False
                if hasattr(self, 'designer'):
                    self.designer.selection = list()
        return super(Field, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.designed and touch.grab_current==self:
            # Here I should watch if shift is set, then it would be an append.
            self.selected = True
            #why parent.parent: because ruled scatter is a scatterlayout: floatlayout + scatter (2 levels)
            if hasattr(self,"designer") and  self.designer.selection and self.designer.selection[0] is not self:
                self.designer.selection[0].selected = False
            if getattr(self, "designer", False):
                self.designer.selection = [self]
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
                if self.selected:
                    self.x += touch.dx
                    self.y += touch.dy
        return RelativeLayout.on_touch_move(self,touch)

    def add_widget(self, widget, index=0):
        #replacing index by z-index
        RelativeLayout.add_widget(self,widget, getattr(widget,'z',0))
        #Duplicate pointer to template
        widget.template = self.template
        #Re order them according to z elt:
        cs = self.children[:]
        cs.sort(key= lambda x: getattr(x,'z',0), reverse=True)
        self.children = cs
        #Also reorder canvas
        for cindex, c in enumerate(self.children):
            if not self.canvas.indexof(c.canvas) == -1:
                self.canvas.remove(c.canvas)
            self.canvas.insert(0,c.canvas)

    def remove_widget(self, widget):
        super(RelativeLayout,self).remove_widget(widget)
        cs = self.children[:]
        cs.sort(key= lambda x: getattr(x,'z',0), reverse=True)
        self.children = cs
        #Also reorder canvas
        for cindex, c in enumerate(self.children):
            self.canvas.remove(c.canvas)
            self.canvas.insert(0,c.canvas)


class FloatField(BaseField, FloatLayout):
    def __init__(self, **kwargs):
        "Create a subclassable list of attributes to display"
        FloatLayout.__init__(self,**kwargs)
        self.derive_infos()

    def on_touch_down(self, touch):
        if self.designed:
            origin = Vector(*touch.pos)
            #Convert origin to take into account self.angle
            for pos in [(self.center_x,self.y+self.sel_radius), (self.center_x, self.top-self.sel_radius),(self.x+self.sel_radius, self.center_y),(self.right-self.sel_radius,self.center_y),(self.right-self.sel_radius, self.top-self.sel_radius),(self.x+self.sel_radius,self.y+self.sel_radius),(self.x+self.sel_radius,self.top-self.sel_radius),(self.right-self.sel_radius,self.y+self.sel_radius)]:
                if self.selected:
                    VECTOR = Vector(*pos)
                    if self.angle:
                        deltapos = Vector(pos[0] - self.center[0], pos[1] - self.center[1])
                        deltapos =  deltapos.rotate(self.angle)
                        VECTOR = deltapos + self.center
                    if origin.distance(VECTOR) <5:
                        touch.ud['do_resize'] = True
                        touch.grab(self)
                        #Calculate the mode of resizing
                        ox,oy = touch.opos
                        cx,cy = self.center
                        touch.ud['LEFT'] = ox<cx
                        touch.ud['DOWN'] = oy<cy
                        if pos in [(self.center_x, self.y+self.sel_radius), (self.center_x, self.top-self.sel_radius)]:
                            touch.ud['movement'] = 'y'
                        if pos in [(self.x+self.sel_radius, self.center_y), (self.right-self.sel_radius, self.center_y)]:
                            touch.ud['movement'] = 'x'
                        if pos in [(self.x+self.sel_radius, self.y+self.sel_radius),(self.x+self.sel_radius, self.top-self.sel_radius), (self.right-self.sel_radius, self.top-self.sel_radius), (self.right-self.sel_radius, self.y+self.sel_radius)]:
                            touch.ud['movement'] = 'xy'
                        return True
            if self.collide_point(*touch.pos):
                touch.grab(self)
                #Define if resized is on
                touch.ud['do_resize'] = False
                #Display params if duoble tap
                if touch.is_double_tap:
                    self.designer.display_field_attributes(self)
                return True
            else:
                self.selected = False
                if hasattr(self, 'designer'):
                    self.designer.selection = list()
        return super(FloatField, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.designed and touch.grab_current==self:
            # Here I should watch if shift is set, then it would be an append.
            self.selected = True
            #why parent.parent: because ruled scatter is a scatterlayout: floatlayout + scatter (2 levels)
            if hasattr(self,"designer") and  self.designer.selection and self.designer.selection[0] is not self:
                self.designer.selection[0].selected = False
            if getattr(self, "designer", False):
                self.designer.selection = [self]
            touch.ungrab(self)
        return super(FloatField, self).on_touch_up(touch)

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
                if self.selected:
                    self.x += touch.dx
                    self.y += touch.dy
        return FloatLayout.on_touch_move(self,touch)

    def add_widget(self, widget, index=0):
        #replacing index by z-index
        FloatLayout.add_widget(self,widget, getattr(widget,'z',0))
        #Duplicate pointer to template
        widget.template = self.template
        #Re order them according to z elt:
        cs = self.children[:]
        cs.sort(key= lambda x: getattr(x,'z',0), reverse=True)
        self.children = cs
        #Also reorder canvas
        for cindex, c in enumerate(self.children):
            if not self.canvas.indexof(c.canvas) == -1:
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

class TextField(Label, FloatField):
    autofit = BooleanProperty(False)
    multiline = BooleanProperty(True)
    max_font_size = NumericProperty()
    min_font_size = NumericProperty()
    halign_values = ['left','center','right','justify']
    valign_values = ['bottom','middle','top']
    attrs = OrderedDict([
        ('text', AdvancedTextEditor), ('autofit', BooleanEditor), ('multiline', BooleanEditor),
        ('max_font_size', IntEditor), ('min_font_size', IntEditor),
        ('color', ColorEditor),
        ('halign',ChoiceEditor), ('valign', ChoiceEditor),
        ('font', FontChoiceEditor) ,
        ('padding_x', IntEditor), ('padding_y', IntEditor)
    ])
    # ('font_size', IntEditor), ('font_name', FontChoiceEditor), ('bold', BooleanEditor),  ('italic', BooleanEditor)])
    #Keep old static font size
    static_font_size = NumericProperty()
    default_attr = "text"
    _single_line_text = StringProperty()

    not_exported = ['static_font_size', 'font', 'text_size', '_single_line_text', 'max_lines']
    font = ListProperty(['DroidSans.ttf', 8,False, False])

    def on_size(self,instance, size):
        self.text_size = size
        self.on_text(instance,self.text)

    def on_autofit(self, instance, autofit):
        if autofit:
            #store the format static value
            self.static_font_size = self.font_size
            #Now calculate the new one
            self.multiline = False
        else:
            #Restore former size, if it exists
            if self.static_font_size:
                self.font_size = self.static_font_size
        self.on_text(instance, None)

    def on_multiline(self, instance, multiline):
        if multiline:
            from textwrap import wrap
            self._single_line_text = self.text
            self.text = '\n'.join(wrap(self.text))
            self.max_lines = 1
        else:
            if self._single_line_text:
                self.text = self._single_line_text
                self.max_lines = 1

    def on_text(self, base, *args):
        self._single_line_text = self.text.replace('\n', '')
        if self.multiline:
            from textwrap import wrap
            self.text = '\n'.join(wrap(self.text))
        else:
            self.text = self._single_line_text
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
            init_fint_size = self.font_size
            #Auto fit to growth
            while self._label.get_extents(self.text)[0]<= self.width and self._label.get_extents(self.text)[1]<= self.height:
                if self.max_font_size and self.font_size>=self.max_font_size:
                    break
                self.font_size+=1
            else:#at taht precise point, if the font size has indeed been increased, their is at least on dimension by which we go too far => shrkink it
                if self.font_size != init_fint_size: #do that only if there has been some changed
                    self.font_size-=1

class ImageField(Image, FloatField):
    attrs = OrderedDict([('source', FileEditor), ('allow_stretch', BooleanEditor), ('keep_ratio', BooleanEditor)])
    not_exported = ['image_ratio', 'texture', 'norm_image_size', 'scale', 'texture_size']
    default_attr = 'source'
    source_filters = ['*.jpg','*.gif','*.jpeg','*.bmp','*.png']

    def on_source(self, instance, source):
        src = find_path(source)
        if src and src != source:
            self.source = src

class ColorField(Field):
    "Display a color on a rectangle"
    rgba=ListProperty((1,1,1,1))
    attrs={'rgba': ColorEditor}
    default_attr = 'rgba'

class BorderField(Field):
    "Draw 4 lines around parent"
    border_width=NumericProperty(1)
    border_color=ListProperty((1,1,1,1))
    border_radius=NumericProperty(0)
    attrs={'border_width': AdvancedIntEditor , 'border_color': ColorEditor, 'border_radius': AdvancedIntEditor}
    default_attr = 'border_color'

class ImgChoiceField(Image, FloatField):
    "This widget will display an image base on a choice, helds in choices dict"
    choices = DictProperty()
    attrs = OrderedDict([('selection',ImgOptionEditor),('choices', ImageChoiceEditor),('allow_stretch', BooleanEditor), ('keep_ratio', BooleanEditor)])
    default_attr = 'selection'
    not_exported = ['image_ratio','texture', 'norm_image_size', 'scale','selection_values','source']
    selection = StringProperty()
    selection_values= ListProperty()

    def on_selection(self, instance, selection):
        if self.choices:
            self.source = find_path(self.choices[selection])

    def on_choices(self, instance, choices):
        self.selection_values = choices.keys()
        if choices and not self.selection:
            self.selection = choices.keys()[0]
        else:
            #force selection
            self.on_selection(self, self.selection)

    def on_source(self, instance, source):
        src = find_path(source)
        if src:
            self.source = src

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

class SymbolField(SymbolLabel, FloatField):
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
        path = find_path(dimension[0])
        if not path: raise ValueError('Invalid path for image to take subimage from', dimension[0])
        IMG = Image(path).texture
        width, height = IMG.width, IMG.height
        self.texture = Image(path).texture.get_region(self.dimension[1]*width,self.dimension[2]*height, self.dimension[3]*width,self.dimension[4]*height)

class TransfoField(Field):#, Image):
    "Transform an image file thourgh different methods registered in img_xfos.py"
    default_attr = 'src'
    not_exported = ['texture', 'Image', 'norm_image_size']
    attrs = {'src': FileEditor, 'xfos': TransfoListEditor}

    texture = ObjectProperty()
    src = ObjectProperty()
    xfos = ListProperty()
    #PIL Image used between xfo
    Image = ObjectProperty(None, allownone = True)

    def on_src(self, instance, src):
        #unbind on old stuff
        #bind on new
        if isinstance(src, BaseField):
            d = dict()
            d[src.default_attr] = self.update
            src.bind(**d)
        if src:
            self.update()

    def update(self,*args):
        #if file path : proceed
        from PIL.Image import frombuffer, FLIP_TOP_BOTTOM
        from kivy.clock import Clock
        SRC = [self.src]
        self.Image = None
        def inner(*args):
            #ugly hack from nonlocal variable in pythnon 2
            source = SRC[0]
            if isinstance(source, basestring):
                source = find_path(source)
                if source:
                    from kivy.core.image import Image as CoreImage
                    cim = CoreImage(source)
                    self.Image = frombuffer('RGBA', cim.size, cim.texture.pixels, 'raw', 'RGBA',0,1)
            elif isinstance(source, BaseField): #widget case
                from kivy.base import EventLoop
                EventLoop.idle()
                from conf import toImage
                cim = toImage(source)
                self.Image = frombuffer('RGBA', cim.size, cim._texture.pixels, 'raw', 'RGBA',0,1)
            if self.Image:
                self.Image.transpose(FLIP_TOP_BOTTOM)
                for xindex, xfo in enumerate(self.xfos):
                    self.Image = xfo(self.Image)
                #Standard mode: flip the
                flip = self.Image.transpose(PILImage.FLIP_TOP_BOTTOM)
                from img_xfos import img_modes
                ktext = Texture.create( size = flip.size)
                ktext.blit_buffer(flip.tobytes(), colorfmt = img_modes[flip.mode])
                self.texture = ktext

        Clock.schedule_once(inner,-1)

    def on_xfos(self, instance, xfos):
        if self.src:
            self.update()

class SvgField(Field):
    source = StringProperty()
    source_filters = ['*.svg']
    attrs = {'source': FileEditor}
    default_attr = 'source'

    def on_source(self,instance, source):
        source = find_path(source)
        if source:
            with self.canvas:
                from kivy.graphics.svg import Svg
                Svg(source)

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

class SourceShapeField(ShapeField):
    skip_designer = True
    source = StringProperty(None)
    source_filters = ('*.png', '*.jpg', '*.jpeg', '*.gif')
    texture = ObjectProperty(None, allownone=True)
    texture_wrap = StringProperty()
    texture_wrap_values = ['repeat', 'mirrored_repeat', 'clamp_to_edge']
    attrs = {'source': FileEditor, 'texture_wrap': ChoiceEditor}
    default_attr = 'source'

    not_exported = ['texture_wrap_values', 'source_filters']

    def on_texture_wrap(self, instance, wrap):
        if self.texture and wrap:
            self.texture.wrap = wrap

    def on_source(self,instance, source):
        from kivy.core.image import Image
        source = find_path(source)
        if source:
            self.texture = Image(source).texture
            self.on_texture_wrap(self, self.texture_wrap)

class LineField(ShapeField):
    #Just goigng from lower left to upper right. is it even useful ?
    pass

class EllipseField(ShapeField):
    angle_start = NumericProperty(0)
    angle_end = NumericProperty(360)
    attrs = OrderedDict([('angle_start', AdvancedIntEditor), ('angle_end', AdvancedIntEditor)])

class RectangleField(ShapeField):
    corner_radius = NumericProperty(0)
    default_attr = 'corner_radius'
    attrs = {'corner_radius': AdvancedIntEditor}

class RectangleFField(SourceShapeField):
    skip_designer = False

class EllipseFField(SourceShapeField):
    skip_designer = False
    angle_start = NumericProperty(0)
    angle_end = NumericProperty(360)
    attrs = OrderedDict([('angle_start', AdvancedIntEditor), ('angle_end', AdvancedIntEditor)])

class WireField(ShapeField):
    attrs = {'points': PointListEditor}
    default_attr = 'points'
    points = ListProperty()

class MeshField(SourceShapeField):
    skip_designer = False
    attrs = {'points': PointListEditor, 'mode': ChoiceEditor}
    default_attr = 'points'
    vertices = ListProperty()
    not_exported = ['vertices']
    points = ListProperty()
    mode = StringProperty('triangle_fan')
    mode_values = 'points', 'line_strip', 'line_loop', 'lines', 'triangle_strip', 'triangle_fan'

    def on_points(self, instance, points):
        from math import cos, sin, pi, radians
        cx, cy = self.pos
        cx,cy = 0,0
        self.vertices = []
        for i in range(0,len(points), 2):
            self.vertices.append(cx + points[i] * self.width)
            self.vertices.append(cy+points[i+1] * self.height)
            #Texture have to be vertically flipped for kivy to load. why ???
            self.vertices.extend([points[i], 1-points[i+1]])

    def on_pos(self, instance, pos):
        self.on_points(instance, self.points)

    def on_size(self, instance, size):
        self.on_points(instance, self.points)

class PolygonField(SourceShapeField):
    #Mesh field with predefined points for regular polygon

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
        cx,cy = self.width/2, self.height/2
        a = 2 * pi / side
        self.vertices = []
        for i in xrange(side):
            self.vertices.extend([
                cx + cos(radians(self.angle_start) + i * a) * float(self.width)/2,
                cy + sin(radians(self.angle_start) + i * a) * float(self.height)/2,
                .5+ 0.5*cos(radians(self.angle_start) + i * a), #cos(radians(self.angle_start) + i * a),
                .5-.5*sin(radians(self.angle_start) + i * a),#sin(radians(self.angle_start) + i * a)
            ])

class BezierField(ShapeField):
    #Unfilled Bezier
    attrs = {'points': PointListEditor}
    default_attr = 'points'
    points = ListProperty()

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

class MaskField(LinkedField):
    # Take a single field and apply a mask based on the source of the mesh
    texture = ObjectProperty(None, allownone=True)

    alpha = NumericProperty(1)

    skip_designer = False
    attrs = {'points': PointListEditor, 'mode': ChoiceEditor}
    default_attr = 'points'
    vertices = ListProperty()
    not_exported = ['vertices']
    points = ListProperty()
    mode = StringProperty('triangle_fan')
    mode_values = 'points', 'line_strip', 'line_loop', 'lines', 'triangle_strip', 'triangle_fan'

    def on_points(self, instance, points):
        from math import cos, sin, pi, radians
        cx, cy = self.pos
        self.vertices = []
        for i in range(0,len(points), 2):
            self.vertices.append(cx + points[i] * self.width)
            self.vertices.append(cy+points[i+1] * self.height)
            #Texture have to be vertically flipped for kivy to load. why ???
            self.vertices.extend([points[i], 1-points[i+1]])


    def add_widget(self, *largs):
        largs= list (largs)
        from kivy.graphics.texture import Texture
        if not hasattr(largs[0],'texture'):
            print 'not texture -> wrapping', largs[0],
            largs[0] = textured(largs[0])
        # trick to attach graphics instructino to fbo instead of canvas
        ret = super(FloatLayout, self).add_widget(*largs)
        self.texture = largs[0].texture
        self.on_points(self, self.points)
        return ret

class EffectField(EffectWidget, LinkedField):
    attrs = {'effects': EffectsEditor}
    default_attr = 'effects'

###############################################
#        Misc                                 #
###############################################

#Texture Item: item which have a texture
class Textured(FloatLayout):
    texture = ObjectProperty()
    texture = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.canvas = Canvas()
        with self.canvas:
            self.fbo = Fbo(size=self.size)
            Color(1, 1, 1)
            self.fbo_rect = Rectangle()

        # wait that all the instructions are in the canvas to set texture
        self.texture = self.fbo.texture
        super(Textured, self).__init__(**kwargs)

    def add_widget(self, *largs):
        # trick to attach graphics instructino to fbo instead of canvas
        canvas = self.canvas
        self.canvas = self.fbo
        ret = super(Textured, self).add_widget(*largs)
        self.canvas = canvas
        return ret

    def remove_widget(self, *largs):
        canvas = self.canvas
        self.canvas = self.fbo
        super(Textured, self).remove_widget(*largs)
        self.canvas = canvas

    def on_size(self, instance, value):
        self.fbo.size = value
        self.texture = self.fbo.texture
        self.fbo_rect.size = value

    def on_pos(self, instance, value):
        self.fbo_rect.pos = value

    def on_texture(self, instance, value):
        self.fbo_rect.texture = value

    def on_alpha(self, instance, value):
        self.fbo_color.rgba = (1, 1, 1, value)

def textured(widget):
    res = Textured()
    res.add_widget(widget)
    res.pos = widget.pos
    res.size = widget.size
    res.size_hint = widget.size_hint
    def info_update(*args):
        res.pos = widget.pos
        res.size = widget.size
    widget.bind(pos=info_update, size=info_update)
    return res

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
                    if pos in [(self.center_x, self.y+5), (self.center_x, self.top-5)]:
                        touch.ud['movement'] = 'y'
                    if pos in [(self.x+5, self.center_y), (self.right-5,self.center_y)]:
                        touch.ud['movement'] = 'x'
                    if pos in [(self.x+5,self.y+5),(self.x+5,self.top-5),(self.right-5, self.top-5), (self.right-5,self.y+5)]:
                        touch.ud['movement'] = 'xy'
                    return True
            if self.collide_point(*touch.pos):
                touch.grab(self)
                #Define if resized is on
                touch.ud['do_resize'] = False
                #Here I should watch if shift is set, then it would be an append.
                return True
        return super(Field, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.designed  and touch.grab_current==self:
            # Here I should watch if shift is set, then it would be an append.
            self.selected = True
            touch.ungrab(self)
        return super(Field, self).on_touch_up(touch)
fieldDict = dict()

for klassName in globals().keys()[:]:
    klass = globals()[klassName]
    if type(klass) == type(Field) and issubclass(klass, BaseField):
        #Remove the shape from this list
        if klass is Field:
            continue
        klass.Type = klassName
        fieldDict[klass.Type] = klass
