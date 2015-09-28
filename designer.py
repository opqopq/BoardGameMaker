"Template Designer interace"
__author__ = 'HO.OPOYEN'


from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.graphics import Color, Line
from kivy.metrics import cm
from kivy.uix.treeview import TreeViewLabel, TreeViewNode
from kivy.properties import ListProperty, DictProperty, ObservableList, ObservableReferenceList, ObservableDict
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup

from fields import Field
from template import BGTemplate, templateList
from conf import card_format, gamepath
from deck import TreeViewField
from os.path import isfile, split, relpath


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

class RuledScatter(ScatterLayout):

    def __init__(self, **kwargs):
        ScatterLayout.__init__(self, **kwargs)
        self.FACTOR_LINE = 1.2
        self.FACTOR_TRIANGLE = .1
        with self.canvas:
            Color(0, 0, 0)
            self.rules = Line(points=[-5,-5, self.width*self.FACTOR_LINE-5,-5, -5,-5, -5, self.height*self.FACTOR_LINE-5])
        self.bind(size=self.draw_rules)

    def draw_rules(self, *args):
        self.rules.points = [-5, -5, self.width*self.FACTOR_LINE-5,-5, -5, -5, -5, self.height*self.FACTOR_LINE-5]
        with self.canvas:
            self.htick = [Line(points=(x*cm(1),-10, x*cm(1),+5)) for x in range(2+int(self.width/cm(1)))]
            self.vtick = [Line(points=(-10, y*cm(1),+5, y*cm(1))) for y in range(2+int(self.height/cm(1)))]

class TreeFieldEntry(TreeViewNode, BoxLayout):
    target = ObjectProperty(None)

class TmplChoicePopup(Popup):
    cb = ObjectProperty()

class BGDesigner(FloatLayout):
    current_template = ObjectProperty(BGTemplate(size=card_format.size))
    selection = ListProperty(rebind=True)
    nodes = DictProperty()
    #Place Holder when copying size/pos of a widget
    _do_copy = None
    #String for holding the path at which template will be saved in the form name@path
    tmplPath = StringProperty()

    def __init__(self, **kwargs):
        super(BGDesigner,self).__init__(**kwargs)
        from kivy.clock import Clock
        def build(*args):
            from fields import fieldDict, ShapeField, LinkedField
            from kivy.factory import Factory
            FE = Factory.get('FieldEntry')
            TFE = Factory.get("TmplFieldEntry")
            PFE = Factory.get('LinkedFieldEntry')
            for key in sorted(fieldDict):
                if hasattr(fieldDict[key], 'skip_designer') and fieldDict[key].skip_designer:
                    continue
                fe = FE()
                fe.text= key
                fe.target = self
                if issubclass(fieldDict[key], ShapeField):
                    if fieldDict[key] == ShapeField:
                        continue
                    self.ids.shapes_stack.add_widget(fe)
                elif issubclass(fieldDict[key], LinkedField):
                    if fieldDict[key] == LinkedField:
                        continue
                    pfe = PFE()
                    pfe.target = self
                    pfe.text = key
                    self.ids.effects_stack.add_widget(pfe)
                else:
                    self.ids.fields_stack.add_widget(fe)
            #Now add Template field
            tfe = TFE()
            tfe.target = self
            self.ids.fields_stack.add_widget(tfe)
            #Forcing current template default size. do not know why
            self.current_template.size = card_format.size

        Clock.schedule_once(build)

    def add_parent_field(self, field):
        "Just like add field, but this parent field will surround the current selection"
        if not self.selection:
            from conf import alert
            alert('Choose a field first', status_color=(1, .43,0.01))
            return
        from fields import fieldDict
        klass = fieldDict.get(field.text, None)
        target = klass()
        child = self.selection[0]
        #Remove it from me
        self.ids.content.remove_widget(child)
        child_node = self.nodes[child]
        self.ids.fields.remove_node(self.nodes[child])
        #Add new field to me
        parent_node = self.insert_field(target)
        self.ids.fields.add_node(child_node, parent_node)
        target.size = child.size
        target.pos = child.pos
        child.pos = 0,0 # move it at parent's origin
        #Now add child back
        target.add_widget(child)
        self.selection = [target,]
        print 'here i should insert field info BELOW parent ! '

    def add_template(self):
        from template import templateList
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.checkbox import CheckBox
        from kivy.uix.button import Button
        from kivy.uix.label import Label
        from kivy.factory import Factory
        from kivy.core.window import Window
        from functools import partial
        cp_width = min(Window.size)*.8
        cp_pos = [(Window.size[0]-cp_width)/2,(Window.size[1]-cp_width)/2]
        tcp = Factory.get('TmplChoicePopup')(pos= cp_pos, size= (cp_width/4,cp_width))
        theList = tcp.ids.tmpl_list
        def cb(sel):
            tcp.dismiss()
            if sel:
                from template import templateList
                tmpl= templateList[sel]
                childrens = tmpl.ids.values()
                node = self.insert_field(tmpl)
                #Deal with Template Properties:
                for pname, editor in tmpl.attrs.items():
                    self.ids.fields.add_node(TreeViewField(name=pname, editor=editor(tmpl)), node)
                #Deal with KV style elemebts
                for fname in tmpl.ids.keys():
                    if not isinstance(tmpl.ids[fname], Field):
                        continue
                    if not tmpl.ids[fname].editable:
                        continue
                    _wid = tmpl.ids[fname]
                    if _wid.default_attr:
                        w = _wid.attrs[_wid.default_attr](_wid)
                        if w is not None:#None when not editable
                            self.ids.fields.add_node(TreeViewField(pre_label=fname, name = _wid.default_attr, editor=w), node)
                #Now for the other ones....
                for field in tmpl.children:
                    if field in childrens:
                        continue
                    if hasattr(field, 'is_context') and getattr(field, 'is_context'):
                        continue
                    #Skip unamed or unwanted field
                    if not field.editable:
                        continue
                    if field.default_attr:
                        w = field.params[field.default_attr](field)
                        if w is not None:#None when not editable
                            pre_label = field.name or field.id or field.Type
                            self.ids.fields.add_node(TreeViewField(pre_label=pre_label, name = field.default_attr, editor=w), node)
                self.selection = [tmpl]
        for tmpl in sorted(templateList.templates):
            b = Button(text=tmpl, size_hint_y=None, height=30)
            b.on_press = partial(cb, tmpl)
            theList.add_widget(b)
        tcp.cb = cb
        tcp.open()

    def add_field(self, field):
        from fields import fieldDict
        klass = fieldDict.get(field.text, None)
        target = klass()
        self.insert_field(target)
        #Select the new field
        self.selection = [target,]

    def insert_field(self, target, parent = None):
        from fields import Field
        #Make Them designer still
        target.designed = True
        target.designer = self
        #why index as a second element: to ensure the order is not reversed
        if parent is None:
            self.ids.content.add_widget(target, len(self.ids.content.content.children))
        else:
            parent.add_widget(target)
        child = self.ids.fields.add_node(TreeFieldEntry(target=target), parent)
        self.nodes[target] = child
        #Way to come back
        child.target = target
        return child

    def display_field_attributes(self,target):
        #Create Nodes based on the menu info of the fields
        nodes_done = set()
        nodes_done.add('styles')
        params = self.ids.params
        #Check if it alreaady exists & if it is me. if yes: skip
        if params.current_field == target:
            return
        params.current_field == target
        params.clear_widgets()
        params.nodes = dict()
        params.root.nodes = [] # as clear widgets does not works
        params.root.text = "%s: %s"%(target.Type,target.name)

        for subNodeName in target.menu:
            subNode = self.ids.params.add_node(TreeViewLabel(text=subNodeName))
            for attr in target.menu[subNodeName]:
                self.ids.params.add_node(TreeViewField(name=attr, editor=target.params[attr](target),size_hint_y= None, height=30), subNode)
                nodes_done.add(attr)
        #Style Node
        self.insert_styles(target)
        #Now for the attributes without menu
        for attr in target.params:
            if attr in nodes_done:
                continue
            self.ids.params.add_node(TreeViewField(name=attr, editor=target.params[attr](target),size_hint_y= None, height=30))

    def insert_styles(self, target):
        style_node = self.ids.params.add_node(TreeViewLabel(text="Style"))
        self.ids.params.add_node(TreeViewField(name='styles', editor=target.params['styles'](target),size_hint_y= None, height=30), style_node)
        for style in target.styles:
            from styles import getStyle
            s_node = self.ids.params.add_node(TreeViewLabel(text=style), style_node)
            sklass = getStyle(style)
            if sklass:
                for param, editor in sklass.attrs.items():
                    self.ids.params.add_node(TreeViewField(name=param, editor=editor(target),size_hint_y= None, height=30), s_node)

    def load(self, templateName):
        #First clean a little
        self.new()
        if '@' in templateName:
            #load from file:
            from template import BGTemplate
            template = BGTemplate.FromFile(templateName)[-1]
        else:
            template = templateList[templateName]
        self.tmplPath = templateName
        #Empty current list
        self.new()
        #Create a c# opy
        self.current_template = template.blank()
        self.ids.tmplName.text = template.name
        #Done by chaging the width & hiehgt tyhingy
        #self.ids.content.size = template.size
        from kivy.metrics import cm
        self.current_template.size = w,h = template.size
        if self.ids.tmpl_unit.text == "cm":
            w/=cm(1)
            h/=cm(1)
        self.ids.tmpl_width.text = "%.2f"%w
        self.ids.tmpl_height.text = "%.2f"%h
        #Have to do that, as chilndre is in the wrong way  !
        ordered_child = [c for c in list(template.walk(restrict= True)) if c.parent == template]
        ordered_child = template.children[:]
        ordered_child.sort(key=lambda x:x.z, reverse=True)
        for target in ordered_child:
            if not isinstance(target, Field):
                #Here we do not import kivy widget; should be replaced by a kivy widget field
                from conf import log
                log("Not importing kivy element %s"%target)
                continue
            template.remove_widget(target)
            self.insert_field(target)

    def new(self,*args):
        for nodeIndex, node in self.nodes.items():
            #self.ids.fields.root.nodes:
            self.ids.fields.remove_node(node)
            self.ids.content.remove_widget(nodeIndex)

        self.current_template = BGTemplate()
        self.ids.tmplName.text = 'TMPL'
        from conf import card_format
        self.current_template.size = card_format.size
        self.ids.content.size = card_format.width, card_format.height
        self.ids.tmpl_width.text = "%.2f"%card_format.width
        self.ids.tmpl_height.text = "%.2f"%card_format.height

    def export_field(self, field, tmpls, imports, level, save_cm, relativ, save_relpath):
        from fields import LinkedField
        prepend = '\t'*level
        #Remove field from any not desired attrbiute for export
        field.prepare_export()
        tmpls.append('\t%s:'%field.Type)
        #Include KV file if templateField
        if isinstance(field, BGTemplate):
            imports.append(field.src)
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
                    if isfile(unicode(value[_v],'latin-1')) and save_relpath:
                        value[_v] = relpath(value[_v], gamepath)
                tmpls.append('%s%s: %s'%(prepend, attr,value))
            elif vtype in (type(tuple()), type(list()), ObservableList, ObservableReferenceList):
                if attr in ("size","pos"):
                    if relativ:
                        tmpls.append('%s%s: %s'%(prepend, attr, compare_to_root(self.current_template.size,value)))
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
                    else:
                        sub.append(str(item))
                tmpls.append('%s%s: '%(prepend, attr) + ', '.join(sub))
            else:
                tmpls.append('%s%s: %s'%(prepend, attr, value))
        if isinstance(field, LinkedField):
            for child_field in field.children:
                if getattr(child_field, 'is_context', False):
                    continue
                print 'todo: child of linked field to process', child_field
        tmpls.append('')

    def save(self,PATH=None,*args):
        from os.path import isfile
        if PATH is None:
            if self.tmplPath:
                PATH = self.tmplPath
                if "@" in PATH:
                    PATH = PATH.split('@')[-1]
                overwrite = True
            else:
                PATH = 'Templates/%s.kv'%self.current_template.name
                overwrite = self.ids.cb_overwrite.active
        else:
            overwrite = self.ids.cb_overwrite.active
        exists = isfile(PATH)
        kv = self.export_kv()
        if overwrite or not exists:
            file(PATH,'wb').write(kv)
        else:
            from conf import alert
            alert('Template %s already exists !'%PATH)
            return
        from conf import alert
        alert('Template %s saved'%self.current_template.name)
        #Force update on deck widget
        from kivy.app import App
        deck = App.get_running_app().root.ids.deck
        stack = deck.ids['stack']
        from template import find_template_path
        for child in stack.children:
            if not hasattr(child, 'template'): continue
            _, tpath = find_template_path(getattr(child, 'template'))
            if tpath.endswith(PATH):
                child.realise()
        print 'todo: how do I save pultiple template on a single KV file ? '

    def export_kv(self):
        #print " -- EXPORT KV  -- "*10
        relativ = self.ids.cb_relative.active
        save_cm = self.ids.cb_cm.active
        save_relpath = self.ids.cb_relpath.active
        imports = list()
        #Will be used to find a interresting base for relpath
        w = self.ids.tmpl_width.text
        h = self.ids.tmpl_height.text
        #Get Unit
        u = self.ids.tmpl_unit.text
        w = float(w)
        h = float(h)
        self.current_template.size = w,h
        if u == 'cm':
            self.current_template.size = w*cm(1), h*cm(1)
        if u == 'cm':
            w *= cm(1)
            h *= cm(1)
            if not save_cm:
                w = "%.2f" % w
                h = "%.2f" % h
        else:
            if save_cm:
                w = "cm(%.2f)"%(w/cm(1))
                h = 'cm(%.2f)'%(h/cm(1))
        if not self.current_template.name:
            self.current_template.name = "TMPL"
        tmpls = ["<%s@BGTemplate>:"%self.current_template.name]
        tmpls.append('\tsize: %s, %s'%(w,h))
        for node in self.ids.fields.root.nodes:
            field = node.target
            self.export_field(field, tmpls, imports, level=2, save_cm=save_cm, relativ=relativ, save_relpath=save_relpath)
        #Prepend include
        if imports:
            tmpls.insert(0, "")
            for imp in imports:
                tmpls.insert(0,"#:include %s"%imp)
        from os import linesep
        print '*'*60
        print "Export KV"
        print linesep.join(tmpls)
        print '*'*60
        return linesep.join(tmpls)

    def on_selection(self, instance, selection):
        tasks = self.ids.tasks
        tasks.clear_widgets()
        if self.selection:
            #First, check if we are copying a pos/size from an old selection
            if self._do_copy:
                field = self.selection[0]
                typ,unit = self._do_copy
                setattr(unit,typ,getattr(field,typ))
                self._do_copy = None
                #Reselect the old one
                self.selection = [unit]
            #Just make sure that the dos are aligned on the widget
            field = self.selection[0]
            children = self.ids.content.content.children
            for widget in children:
                if widget == field:
                    if widget.designed:
                        widget.selected = True
                    continue
                if widget.selected and widget.designed:
                    widget.selected = False

            #Add some button around me
            from kivy.factory import Factory
            from kivy.uix.label import Label
            #Now for the big show
            text = field.name if field.name else field.Type
            if text.lower().endswith('field'):
                text= text[:-5]
            label = Label(text=text, size_hint_x=None, width = 100)
            tasks.add_widget(label)

            ftb = Factory.get('FieldTaskButton')
            data=[
                (self.remove_selection, 'img/Deleteblack.png'),
                (self.duplicate_selection, 'img/duplicate.png'),
            ]
            for cb, img in data:
                _button = ftb()
                _button.source = img
                _button.bind(on_press=cb)
                _button.designer = self
                tasks.add_widget(_button)
            ##self.insertMoveUpDownButton()
            IMGS = Factory.get('ImageSpinner')
            img_spinner = IMGS(text='Position')
            img_spinner.bind(text = self.position_selection)
            tasks.add_widget(img_spinner)
            img_spinner.values=['Left', 'Right', 'Top', 'Bottom', 'Center H', 'Center V', 'Copy']
            img_spinner = IMGS(text='Size')
            img_spinner.bind(text = self.align_selection)
            tasks.add_widget(img_spinner)
            img_spinner.values=['Max H', 'Max V', 'Copy']
            #Now load the specific attributes matrix/tree for field 6> activated by a double tap on the field
            ##self.display_field_attributes(field)

    def insertMoveUpDownButton(self):
        from kivy.factory import Factory
        field = self.selection[0]
        children = self.ids.content.content.children
        ftb = Factory.get('FieldTaskButton')
        tasks = self.ids.tasks
        #Move Up/Down for z index
        if field in children:
            mub = ftb()
            mub.source = 'img/arrow_up.png'
            if not children.index(field):#
                mub.disabled = True
                mub.opacity = .5
            else:
                mub.bind(on_press=self.move_up_selection)
            mdb = ftb()
            mdb.source = 'img/arrow_down.png'
            if children.index(field)+1 == len(children):
                #Last one
                mdb.disable = True
                mdb.opacity = .5
            else:
                mdb.bind(on_press=self.move_down_selection)
            #Resume
            tasks.add_widget(mub)
            tasks.add_widget(mdb)

    def position_selection(self,*args):
        pos= args[1]
        conv ={'Left': 'x', 'Bottom': 'y', 'Center H': 'center_x', 'Center V': 'center_y'}
        attr = conv.get(pos, pos.lower())
        if self.selection:
            unit = self.selection[0]
            if attr=='copy':
                from conf import alert
                alert('Choose target to copy pos from')
                self._do_copy =('pos', unit)
            else:
                setattr(unit, attr, getattr(unit.parent,attr))

    def align_selection(self, *args):
        pos = args[1]
        if self.selection:
            unit = self.selection[0]
            if pos == 'Max H':
                unit.width = unit.parent.width
                unit.x = unit.parent.x
            elif pos == 'Max V':
                unit.height= unit.parent.height
                unit.y= unit.parent.y
            elif pos == 'Copy':
                from conf import alert
                alert('Choose target to copy size from')
                self._do_copy =('size', unit)

    def duplicate_selection(self,*args):
        if self.selection:
            unit= self.selection[0]
            copy = unit.Copy()
            ##self.insert_field(copy)
            #Select the new field
            ##self.selection = [copy]

    def remove_selection(self,*args):
        if self.selection:
            unit = self.selection[0]
            self.ids.content.remove_widget(unit)
            self.ids.fields.remove_node(self.nodes[unit])
            del self.selection[0]

    def move_up_selection(self,*args):
        if self.selection:
            unit = self.selection[0]
            children = self.ids.content.content.children
            cindex = children.index(unit)
            for node in self.nodes.values():
                self.ids.fields.remove_node(node)
            self.ids.content.content.remove_widget(unit)
            self.ids.content.content.add_widget(unit, index=cindex-1)
            #children[cindex], children[cindex-1] = children[cindex-1],children[cindex]
            for child in children:
                self.ids.fields.add_node(self.nodes[child])
            self.on_selection(None,None)

    def move_down_selection(self,*args):
        if self.selection:
            unit = self.selection[0]
            children = self.ids.content.content.children
            cindex = children.index(unit)
            for node in self.nodes.values():
                self.ids.fields.remove_node(node)
            #children[cindex], children[cindex+1] = children[cindex+1],children[cindex]
            self.ids.content.content.remove_widget(unit)
            self.ids.content.content.add_widget(unit, index=cindex+1)
            for child in children:
                self.ids.fields.add_node(self.nodes[child])
            self.on_selection(None,None)

    def change_tmpl_unit(self):
        from kivy.metrics import cm
        #Get text
        w = self.ids.tmpl_width.text
        h = self.ids.tmpl_height.text
        #Get Unit
        u = self.ids.tmpl_unit.text
        try:
            w = float(w)
            h = float(h)
            if u == 'cm':
                self.ids.tmpl_width.text = "%.2f"%(w/cm(1))
                self.ids.tmpl_height.text = "%.2f"%(h/cm(1))
            else:
                self.ids.tmpl_width.text = "%.2f"%(w*cm(1))
                self.ids.tmpl_height.text = "%.2f"%(h*cm(1))
        except Exception,E:
            from conf import log
            log(E)

    def update_tmpl_size(self):
        from kivy.metrics import cm
        #Get text
        w = self.ids.tmpl_width.text
        h = self.ids.tmpl_height.text
        #Get Unit
        u = self.ids.tmpl_unit.text
        try:
            w = float(w)
            h = float(h)
            if u =='cm':
                w = cm(w)
                h = cm(h)
        except ValueError, E:
            return
        self.current_template.size=w,h
        self.ids.content.size = w,h

from kivy.uix.treeview import TreeView
class FieldTreeView(TreeView):
    def on_selected_node(self, instance, selected_node):
        if selected_node:
            if hasattr(selected_node,'target'):
                self.designer.selection = [selected_node.target]
                self.designer.display_field_attributes(selected_node.target)

#Need to put it at the end because klass needed in kv
Builder.load_file('kv/designer.kv')
