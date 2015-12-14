"""Contains all the diffrents fields for template"""

from collections import OrderedDict
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage, Image
from kivy.factory import Factory
from kivy.properties import ObservableDict, ObservableList, ObservableReferenceList
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics.texture import Texture
from kivy.uix.behaviors import FocusBehavior
from kivy.graphics import Color, Rectangle, Canvas
from kivy.graphics.fbo import Fbo
from utils.symbol_label import SymbolLabel
from kivy.uix.effectwidget import EffectWidget
from editors import *
from conf import gamepath
from utils import find_path, toImage
from os.path import relpath
from kivy.uix.widget import WidgetMetaclass
from kivy.uix.relativelayout import RelativeLayout
from styles import getStyle # Pre-import styles to register them all

###############################################
#        Field                                #
###############################################


def get_hint(rootsize, fieldsize, is_pos=False):
    """Take 2 size or pos tuple and return a tuple made of size_hint of pos_hint"""
    xa, ya = rootsize
    xb, yb = fieldsize
    assert xa and ya
    xratio = float(xb)/float(xa)
    yratio = float(yb)/float(ya)
    rounded_x = round(xratio,2)
    rounded_y = round(yratio,2)
    if is_pos:
        return {'x': rounded_x, 'y': rounded_y}
    return rounded_x, rounded_y


class MetaField(WidgetMetaclass):
    def __new__(meta, name, bases, dct):
        #print bases
        #print dct
        #Compute menu & params
        params = OrderedDict()
        menu = OrderedDict()
        for klass in reversed(bases):
            if not(hasattr(klass, '__metaclass__')) or klass.__metaclass__ != MetaField:
                continue
            for k,v in klass.params.items():
                params[k] = v
            for k,v in klass.menu.items():
                menu[k] = v
        if 'attrs' in dct:
            params.update(dct['attrs'])
        if '_menu' in dct:
            menu.update(dct['_menu'])
        dct['default_attr_values'] = params.keys()
        dct['params'] = params
        dct['menu'] = menu
        return super(MetaField, meta).__new__(meta, name, bases, dct)


class BaseField(FocusBehavior):
    """Element class represent any component of a template (fields, font, transformation....)"""
    __metaclass__ = MetaField
    skip_designer = True

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
            ('opacity', AdvancedRangeEditor), ('angle',AdvancedIntEditor), ('bg_color',ColorEditor),('editable', BooleanEditor), ('printed', BooleanEditor), ('default_attr', ChoiceEditor), ("styles", StyleEditor)
    ])
    #Default Attr is the name of the attribute that souhld be editable in the deck editor (vs all in designer). Several one, if a list
    default_attr = ""
    #List of attr name for this class that should not be exported from designer
    not_exported = ['template', "directives", "code_behind", 'sel_radius', 'cls',
                    'focus','focused', 'width','height','parent','designed','children',
                    'selected','right','border_point','hovered', 'top','center','center_x','center_y','x','y',
                    'texture', 'texture_size', 'Type', 'size_hint_x','size_hint_y',
                    #Stuff from contextnehavior
                    '_requested_keyboard','keyboard','_keyboard',
                    ]

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
    _menu = OrderedDict([('Object',['name','editable','printed','default_attr']),("Shape",['x','y','z','width','height','size_hint', 'pos_hint','opacity','angle','bg_color'])])

    Type = 'Field'

    #place to hold all kv codes from designeer
    code_behind = DictProperty()

    #Includes all the directives, like import or set.
    directives = ListProperty()

    #Pointer to the template we are part of. easier for evaluating context of a template
    template = ObjectProperty()

    #Boolean to remove field right beffore printing.
    printed = BooleanProperty(True)

    def on_focus(self,instance, focus):
        if self.designed and focus:
            self.selected = focus
            try:
                self._bind_keyboard()
            except KeyError:
                pass
        else:
            try:
                self._unbind_keyboard()
            except KeyError:
                pass

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

        #it should be noted that, if rule are suppressed from styles, then the widget will not diretly reflect that

    def on_designed(self,instance, designed):
        if designed:
            drule = [x for x in Builder.rules if x[0].key == 'designed'][0][1]
            Builder._apply_rule(self, drule, drule)
            #Change relative pos-hint /size hint for
            if self.pos_hint:
                if not 'x' in self.pos_hint:
                    self.pos_hint['x'] = 0
                if not 'y' in self.pos_hint:
                    self.pos_hint['y'] = 0
                self.pos = self.pos_hint['x']*self.parent.width, self.pos_hint['y'] * self.parent.height
                self.pos_hint = {}
            if self.size_hint != [None, None]:
                if self.size_hint[0] is None:
                    w = 100
                else:
                    w = self.size_hint[0]*self.parent.width
                if self.size_hint[1] is None:
                    h = 100
                else:
                    h = self.size_hint[1]*self.parent.height
                self.size =  w, h
                self.size_hint = None, None

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
        self.code_behind = dict()

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
        if self.name:
            blank.name = self.name +'-copy'
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
            dad = self.parent
            cs = self.parent.children[:]
            cs.sort(key=lambda x: x.z)
            self.parent.clear_widgets()
            for c in cs:
                dad.add_widget(c)

            ##self.parent.children= cs
            ###Also reorder canvas
            ##for c in cs:
            ##    self.parent.canvas.remove(c.canvas)
            ##    self.parent.canvas.insert(0,c.canvas)

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
        changes_attrs = field.getChangedAttributes(True)
        if 'size_hint' in changes_attrs:
            if 'size' in changes_attrs:
                changes_attrs.remove("size")
        if 'pos_hint' in changes_attrs:
            if 'pos' in changes_attrs:
                changes_attrs.remove('pos')
        for attr in changes_attrs:
            #Check if code behind:
            if attr in field.code_behind:
                print 'Attr %s has been changed and should be written down. One could write the code behind:'%attr, field.code_behind[attr]
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
                        tmpls.append('%s%s: %s'%(prepend, "%s_hint"%attr, get_hint(self.template.size,value, attr=='pos')))
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
        # #Special Case: how to handle ids value for BGTemplate, which are both name & subfield
        # if isinstance(field, BGTemplate):
        #     b = field.blank()
        #     for child in self.ids:
        #         _b,_c = getattr(b.ids,child), getattr(self.ids,child)
        #         _bv = getattr(_b,_b.default_attr)
        #         _cv = getattr(_c, _c.default_attr)
        #         if _bv != _cv:
        #             if isinstance(_cv, float):
        #                 _pcv = '%.2f'%_cv
        #             elif isinstance(_cv, basestring):
        #                 if isfile(_cv) and save_relpath:
        #                     _pcv = '"%s"'%relpath(_cv, gamepath)
        #                 else:
        #                     _pcv = '"%s"'%_cv
        #             elif isinstance(_cv, FunctionType): #replace the function by its name without the ""
        #                 _pcv = '%s'%_cv.func_name
        #             else:
        #                 _pcv = str(_cv)
        #             tmpls.append('%s%s:'%(prepend,child))
        #             tmpls.append('\t%s%s: %s'%(prepend, _c.default_attr, _pcv))
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

class Field( BaseField, RelativeLayout):
    skip_designer = True

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
                        deltapos = deltapos.rotate(self.angle)
                        VECTOR = deltapos + self.center
                    if origin.distance(VECTOR) <5:
                        touch.ud['do_move'] = False
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
                touch.ud['do_move'] = False
                #Display params if duoble tap
                if touch.is_double_tap and hasattr(self, 'designer'):
                    self.designer.display_field_attributes(self)
                return True
            #else:
                #self.selected = False
                #if hasattr(self, 'designer'):
                #    if self in self.designer.selection: del self.designer.selection[self.designer.selection.index(self)]
                #    #self.designer.selection = list()
        return super(Field, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.designed and touch.grab_current == self:
            if getattr(self, "designer", False):
                if self in self.designer.selections and not(touch.ud['do_resize'] or touch.ud['do_move']):
                    del self.designer.selections[self]
                    if self.designer.last_selected == self:
                        self.designer.last_selected = None
                else:
                    self.designer.selections[self] = None
                    self.designer.last_selected = self
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
                touch.ud['do_move'] = True
                if self.selected:
                    self.x += touch.dx
                    self.y += touch.dy

                    if self.designed:
                        if getattr(self, 'designer', False):
                            for c in self.designer.selections:
                                if c == self:
                                    continue
                                c.x += touch.dx
                                c.y += touch.dy
        return RelativeLayout.on_touch_move(self,touch)

    def add_widget(self, widget, index=0):
        #Duplicate pointer to template
        widget.template = self.template
        #Re order them according to z elt:
        cs = self.children[:]
        cs.append(widget)
        cs.sort(key= lambda x: getattr(x,'z',0))
        self.clear_widgets()
        for c in cs:
            RelativeLayout.add_widget(self, c)
        # self.children = cs
        # #Also reorder canvas
        # for cindex, c in enumerate(self.children):
        #     if not self.canvas.indexof(c.canvas) == -1:
        #         self.canvas.remove(c.canvas)
        #     self.canvas.insert(0,c.canvas)


class FloatField(BaseField, FloatLayout):
    skip_designer = True

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
                    if origin.distance(VECTOR) < 5:
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
                touch.ud['do_move'] = False
                #Display params if duoble tap
                if touch.is_double_tap and hasattr(self, 'designer'):
                    self.designer.display_field_attributes(self)
                return True
            # else:
            #     self.selected = False
            #     if hasattr(self, 'designer'):
            #         if self in self.designer.selection: del self.designer.selection[self.designer.selection.index(self)]
            #     #    self.designer.selection = list()
        return super(FloatField, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.designed and touch.grab_current==self:
            if getattr(self, "designer", False):
                if self in self.designer.selections and not(touch.ud['do_resize'] or touch.ud['do_move']):
                    del self.designer.selections[self]
                    if self.designer.last_selected == self:
                        self.designer.last_selected = None
                else:
                    self.designer.selections[self] = None
                    self.designer.last_selected = self
            if getattr(self, "layout_maker", False):
                self.layout_maker.selections[self] = None
                self.layout_maker.selected_ph = self
            touch.ungrab(self)
        return super(FloatField, self).on_touch_up(touch)

    def on_touch_move(self, touch):
        if self.designed and touch.grab_current == self:
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
                touch.ud['do_move'] = True
                if self.selected:
                    self.x += touch.dx
                    self.y += touch.dy
                    if self.designed:
                        if getattr(self, 'designer', False):
                            for c in self.designer.selections:
                                if c == self:
                                    continue
                                c.x += touch.dx
                                c.y += touch.dy
        return FloatLayout.on_touch_move(self,touch)

    def add_widget(self, widget, index=0):
        ##replacing index by z-index
        #Duplicate pointer to template
        widget.template = self.template
        #Re order them according to z elt:
        cs = self.children[:]
        cs.append(widget)
        self.clear_widgets()
        cs.sort(key= lambda x: getattr(x,'z',0))
        for c in cs:
            FloatLayout.add_widget(self,widget)
        #self.children = cs
        ##Also reorder canvas
        #for cindex, c in enumerate(self.children):
        #    if not self.canvas.indexof(c.canvas) == -1:
        #        self.canvas.remove(c.canvas)
        #    self.canvas.insert(0,c.canvas)

    def Oremove_widget(self, widget):
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
    font_color = ListProperty([1,1,1,1])
    halign_values = ['left','center','right','justify']
    valign_values = ['bottom','middle','top']
    attrs = OrderedDict([
        ('text', RichTextEditor), ('autofit', BooleanEditor), ('multiline', BooleanEditor),
        ('font_color', ColorEditor),
        ('halign',ChoiceEditor), ('valign', ChoiceEditor),
        ('font', FontChoiceEditor) , ('markup', BooleanEditor),
        ('max_font_size', IntEditor), ('min_font_size', IntEditor),
        ('padding_x', IntEditor), ('padding_y', IntEditor)
    ])
    # ('font_size', IntEditor), ('font_name', FontChoiceEditor), ('bold', BooleanEditor),  ('italic', BooleanEditor)])
    #Keep old static font size
    static_font_size = NumericProperty()
    default_attr = "text"
    _single_line_text = StringProperty()

    not_exported = ['static_font_size', 'font', 'text_size', '_single_line_text', 'max_lines']
    font = ListProperty(['default', 8,False, False])

    _menu = {'Font': ['font', 'font_color', 'autofit', 'max_font_size', 'min_font_size', 'padding_x', 'padding_y']}

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
        #Force label create
        self._single_line_text = self.text.replace('\n', '')
        if self.multiline:
            from textwrap import wrap
            #self.text = '\n'.join(wrap(self.text))
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


class SymbolField(SymbolLabel, TextField):
    attrs = {'symbols': ImageChoiceEditor}


class ImageField(AsyncImage, FloatField):
    attrs = OrderedDict([
        ('source', FileEditor),
        ('allow_stretch', BooleanEditor),
        ('keep_ratio', BooleanEditor)
    ])
    not_exported = ['image_ratio', 'texture', 'norm_image_size', 'scale', 'texture_size']
    default_attr = 'source'
    source_filters = ['*.jpg','*.gif','*.jpeg','*.bmp','*.png']

    def on_source(self, instance, source):
        src = find_path(source)
        if src and src != source:
            self.source = src


class ImgChoiceField(AsyncImage, FloatField):
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
            if not self.selection in choices:
                self.selection = choices.keys()[0]
            self.on_selection(self, self.selection)

    def on_source(self, instance, source):
        src = find_path(source)
        if src:
            self.source = src


class RepeatField(FloatField):
    """x_func & y_func recognize row,col & index variable. They should emit a pos_hint value (between 0 & 1) that will be added to the current pos_hint"""
    allow_stretch = BooleanProperty(True)
    keep_ratio = BooleanProperty(False)
    count = NumericProperty(1)
    images= DictProperty()
    orientation = StringProperty('lr-tb')
    orientation_values = ['lr-tb','tb-lr','bt-lr','lr-bt', 'random']
    x_func = StringProperty()
    y_func = StringProperty()
    target_ratio = ListProperty([1,1])
    angle_step = NumericProperty()
    attrs = OrderedDict([('count',AdvancedIntEditor),('images',ImageChoiceEditor),
                         ('orientation',ChoiceEditor),('target_ratio',SizeHintEditor),
                         ('allow_stretch',BooleanEditor), ('keep_ratio',BooleanEditor),
                         ('angle_step', AdvancedIntEditor),
                         ('x_func',AdvancedTextEditor),('y_func',AdvancedTextEditor),
                         ])

    def on_images(self, instance, value):
        self.update()

    def on_x_func(self,instance, value):
        self.update()

    def on_y_func(self, instance, value):
        self.update()

    def on_count(self, instance, value):
        self.update()

    def on_orientation(self, instance, value):
        self.update()

    def on_size(self,instance,value):
        self.update()

    def add_obj(self):
        obj = ImageField(allow_stretch = self.allow_stretch, keep_ratio = self.keep_ratio)
        obj.size_hint = self.target_ratio
        self.add_widget(obj)
        return obj

    def on_angle_step(self, instance, value):
        self.update()

    def on_target_ratio(self,instance,value):
        self.update()

    def update(self):
        from itertools import cycle
        self.clear_widgets()
        if not self.images:
            return
        #Create x/y delta func
        if not self.x_func:
            xf = lambda r, c, ang: 0
        else:
            def xf(row, col, index):
                from kivy.metrics import cm
                return eval(self.x_func)
        if not self.y_func:
            yf = lambda r, c, ang: 0
        else:
            def yf(row, col, index):
                from kivy.metrics import cm
                return eval(self.y_func)

        wr,hr = self.target_ratio
        ANGLE = -self.angle_step # In order to make sure that first pasted image will have an angle of 0
        if self.orientation == 'random':
            from random import random
            for index,img in zip(range(self.count),cycle(self.images)):
                obj = self.add_obj()
                obj.pos_hint = {'x': random() * (1-wr), 'y': random() * (1-hr)}
                ANGLE += self.angle_step
                obj.angle = ANGLE%360
                obj.source = self.images[img]
        else:
            num_col = int(round(1/wr))
            num_row = int(round(1/hr))
            cyc = cycle(self.images)
            index = 0
            if self.orientation.endswith('lr'):
                for i in range(num_col):
                    for j in range(num_row):
                        index += 1
                        if index>self.count:
                            break
                        obj = self.add_obj()
                        obj.source = self.images[cyc.next()]
                        ANGLE += self.angle_step
                        obj.angle = ANGLE%360
                        if self.orientation.startswith('bt'):
                            obj.pos_hint = {'x': wr * i + xf(i, j, index), 'y': hr * j + yf(i, j, index)}
                        else:
                            obj.pos_hint = {'x': wr * i + xf(i, j, index), 'top': (1 - hr * j) + yf(i, j, index)}
            else: #col first
                for j in range(num_row):
                    for i in range(num_col):
                        index += 1
                        if index>self.count:
                            break
                        obj = self.add_obj()
                        obj.source = self.images[cyc.next()]
                        ANGLE += self.angle_step
                        obj.angle = ANGLE%360
                        if self.orientation.endswith('bt'):
                            obj.pos_hint = {'x': wr * i + xf(i, j, index) , 'y': hr * j + yf(i, j, index)}
                        else:
                            obj.pos_hint = {'x': wr*i + xf(i, j, index), 'top': 1-hr*j + yf(i, j, index)}


class ColorField(Field):
    "Display a color on a rectangle"
    rgba=ListProperty((1,1,1,1))
    attrs={'rgba': ColorEditor}
    default_attr = 'rgba'


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
        if not path:
            from utils import log
            log("Invalid path for source of SubImage %s:%s"%(self,dimension[0]))
            return
            from kivy.graphics.texture import Texture
            self.texture = Texture.create(size=(100,100))
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
                from utils import toImage
                cim = toImage(source)
                self.Image = frombuffer('RGBA', cim.size, cim._texture.pixels, 'raw', 'RGBA',0,1)
            if self.Image:
                self.Image.transpose(FLIP_TOP_BOTTOM)
                for xindex, xfo in enumerate(self.xfos):
                    self.Image = xfo(self.Image)
                #Standard mode: flip the
                flip = self.Image.transpose(FLIP_TOP_BOTTOM)
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

#class LineField(ShapeField):
#    #Just goigng from lower left to upper right. is it even useful ?
#    pass


class RectangleField(SourceShapeField):
    #A value of corner radius. Same for all corner. Might evolve to a multiple value later on
    corner_radius = NumericProperty(0)
    #inside_border: set to True if you want the border to be drawned inside the rectangle
    inside_border = BooleanProperty(False)
    attrs = {'corner_radius': AdvancedIntEditor, 'inside_border': BooleanEditor, 'fg_color': ColorEditor}
    fg_color = ListProperty([1,1,1,1])


class BorderField(RectangleField):
    "Draw 4 lines around parent"

    #Turn Auto COlor to yes if you want the border to adapt its color to the dominant color of it source image
    auto_color = BooleanProperty(False)
    attrs={'auto_color': BooleanEditor}

    def on_source(self,instance, source):
        super(BorderField,self).on_source(instance,source)
        #Replace fg color by transparent color
        Logger.debug('Change FG color to trnasparent when adding source in %s'%self)
        r,g,b,a = self.fg_color
        self.fg_color = r,g,b,0
        self.on_auto_color(self,self.auto_color)

    def on_auto_color(self,instance, value):
        if value:
            if self.source:
                from utils.kmeans import colorz
                res = colorz(self.source, n=1)
                from kivy.utils import get_color_from_hex
                self.line_color = get_color_from_hex(res[0])


class GridField(ShapeField):
    cols = NumericProperty(5)
    rows = NumericProperty(5)
    attrs = {'cols': AdvancedIntEditor, 'rows': AdvancedIntEditor} #, 'images': ImageChoiceEditor}
    points = ListProperty()
    images = DictProperty()
    not_exported = ['points']

    def on_cols(self, instance, value):
        self.update_points()

    def on_rows(self, instance, value):
        self.update_points()

    def on_pos(self, instance, value):
        self.update_points()

    def on_size(self, instance, value):
        self.update_points()

    def on_images(self, instance, value):
        self.update_points()

    def update_points(self):
        self.clear_widgets()
        points = list()
        for i in range(self.cols):
            if i%2:
                points.extend((self.x+(i*self.width/self.cols),self.top))
                points.extend((self.x+(i*self.width/self.cols),self.y))
                #points.append(self.x+(i+1*self.width/self.cols),self.y)
            else:
                points.extend((self.x+(i*self.width/self.cols),self.y))
                points.extend((self.x+(i*self.width/self.cols),self.top))
                #points.append(self.x+(i+1*self.width/self.cols),self.top)
        #Rebase thinks to start from lower right
        if self.cols%2:
            points.extend((self.right, self.top))
        for j in range(self.rows):
            if j%2:
                points.extend((self.x, self.y+(j*self.height/self.rows)))
                points.extend((self.right, self.y+(j*self.height/self.rows)))
            else:
                points.extend((self.right, self.y+(j*self.height/self.rows)))
                points.extend((self.x, self.y+(j*self.height/self.rows)))
        self.points = points
        #Now, try to stick as much image as possible:
        imgs = sorted(self.images.keys(), reverse=True)
        from kivy.uix.image import Image
        for i in range(self.cols):
            for j in range(self.rows):
                if not imgs:
                    return
                img = imgs.pop()
                self.add_widget(Image(keep_ratio=False, allow_stretch=True,source=self.images[img], size=(self.width/max(self.cols,1),(self.height/max(self.rows,1))), pos=(self.x+i*self.width/max(1, self.cols),self.y+j*self.height/max(1,self.rows))))


class EllipseField(SourceShapeField):
    angle_start = NumericProperty(0)
    angle_end = NumericProperty(360)
    fg_color = ListProperty([1,1,1,1])
    attrs = OrderedDict([('fg_color', ColorEditor), ('angle_start', AdvancedIntEditor), ('angle_end', AdvancedIntEditor)])


class WireField(ShapeField):
    attrs = {'points': PointListEditor}
    default_attr = 'points'
    points = ListProperty()


class MeshField(SourceShapeField):
    attrs = {'points': PointListEditor, 'mode': ChoiceEditor}
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
    "Abstrat class used to point out field that have children"
#
# class CopyField(LinkedField):
#     target = ObjectProperty()
#     skip_list = ListProperty(['name'])
#     default_attr = 'target'
#     attrs = {'target': FieldEditor}
#     # No type: will be overidden by target
#     not_exported = ['target', 'skip_list']
#
#     def callback_setter(self, src, dst, attr):
#         def inner(instance, value):
#             #print 'forwarding %s (%s) from %s to %s / %s' % (attr,value, src, instance, dst)
#             setattr(dst, attr, value)
#         return inner
#
#     def on_target(self, instance, target):
#         blank = target.__class__()
#         self.add_widget(blank)
#         # First, bind all params from target to blank
#         for attr in target.params:
#             if not attr in target.properties():
#                 continue
#             kw = {attr: self.callback_setter(attr=attr, src=target, dst= blank)}
#             try:
#                 target.unbind(**kw)
#             except KeyError: # binding does not exists
#                 pass
#             if attr in self.skip_list:
#                 continue
#             # Copy value
#             try:
#                 setattr(blank, attr, getattr(target, attr))
#             except Exception, E:
#                 import traceback
#                 print 'Error while duplicating ', blank, attr, getattr(target,attr), ' Exception raised:',E
#                 traceback.print_exc()
#             target.bind(**kw)
#         # Then bind all params from ME to blank
#         for attr in self.params:
#             if attr in ('target', 'parent', 'skip_list', 'default_attr', 'attrs'):
#                 continue
#             if attr not in target.properties():
#                 continue
#             kw = {attr: self.callback_setter(attr=attr, src=self, dst=blank)}
#             try:
#                 self.unbind(**kw)
#             except KeyError:  # binding does not exists
#                 pass
#             # Copy value
#             try:
#                 setattr(blank, attr, getattr(self, attr))
#             except Exception, E:
#                 import traceback
#                 print 'Error while conveying', blank, attr, getattr(self,attr), ' Exception raised:',E
#                 from conf import log
#                 log(E, traceback.format_exc())
#             self.bind(**kw)

class MaskField(LinkedField):
    # Take a single field and apply a mask based on the source of the mesh
    texture = ObjectProperty(None, allownone=True)

    alpha = NumericProperty(1)

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


Builder.load_file('kv/fields.kv')
