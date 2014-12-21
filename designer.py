"Template Designer interace"
__author__ = 'HO.OPOYEN'


from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.graphics import Color, Line
from kivy.metrics import cm
from kivy.uix.treeview import TreeViewLabel, TreeViewNode
from kivy.properties import ListProperty, DictProperty, ObservableList, ObservableReferenceList
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup

from fields import Field
from template import BGTemplate, templateList
from conf import card_format
from deck import TreeViewField
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
        print 'removing child', child
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
        #Now, for each attributes, add it to the list
        #Create Nodes based on the menu info of the fields
        nodes_done = set()
        nodes_done.add('styles')
        for subNodeName in target.menu:
            subNode = self.ids.fields.add_node(TreeViewLabel(text=subNodeName), child)
            for attr in target.menu[subNodeName]:
                self.ids.fields.add_node(TreeViewField(name=attr, editor=target.params[attr](target),size_hint_y= None, height=30), subNode)
                nodes_done.add(attr)
        #Style Node
        self.insert_styles(target, child)
        #Now for the attributes without menu
        for attr in target.params:
            if attr in nodes_done:
                continue
            self.ids.fields.add_node(TreeViewField(name=attr, editor=target.params[attr](target),size_hint_y= None, height=30), child)

        return child

    def insert_styles(self, target, child):
        style_node = self.ids.fields.add_node(TreeViewLabel(text="Style"), child)
        for node in style_node.nodes:
            self.ids.fields.remove_node(node)
        self.ids.fields.add_node(TreeViewField(name='styles', editor=target.params['styles'](target),size_hint_y= None, height=30), style_node)
        for style in target.styles:
            from styles import getStyle
            s_node= self.ids.fields.add_node(TreeViewLabel(text=style), style_node)
            sklass = getStyle(style)
            if sklass:
                for param, editor in sklass.attrs.items():
                    self.ids.fields.add_node(TreeViewField(name=param, editor=editor(target),size_hint_y= None, height=30), s_node)

    def load(self, templateName):
        print 'see if there is a better way to moving the template around. maybe a copy ?'
        template = templateList[templateName]
        #Empty current list
        self.new()
        #Create a c# opy
        self.current_template = template.blank()
        self.ids.tmplName.text = template.name
        #Done by chaging the width & hiehgt tyhingy
        #self.ids.content.size = template.size
        from kivy.metrics import cm
        w,h = template.size
        if self.ids.tmpl_unit.text == "cm":
            w/=cm(1)
            h/=cm(1)
        self.ids.tmpl_width.text = "%.2f"%w
        self.ids.tmpl_height.text = "%.2f"%h
        #Have to do that, as chilndre is in the wrong way  !
        ordered_child = [c for c in list(template.walk(restrict= True)) if c.parent == template]
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
        self.ids.content.size = card_format.width, card_format.height
        self.ids.tmpl_width.text = "%.2f"%card_format.width
        self.ids.tmpl_height.text = "%.2f"%card_format.height

    def export_field(self, field, tmpls, imports, level):
        from fields import LinkedField
        prepend = '\t'*level
        #Remove field from any not desired attrbiute for export
        field.prepare_export()
        tmpls.append('\t%s:'%field.Type)
        #Include KV file if templateField
        if isinstance(field, BGTemplate):
            imports.append(field.src)
        for attr in field.getChangedAttributes(restrict=True):
            #convert name to ID
            if attr == 'name':
                tmpls.append('%sid: %s'%(prepend,getattr(field,attr)))
            elif type(getattr(field, attr))==type(""):
                tmpls.append('%s%s: "%s"'%(prepend,attr, getattr(field,attr)))
            elif type(getattr(field, attr))==type(1.0):
                tmpls.append('%s%s: %.2f'%(prepend, attr, getattr(field,attr)))
            elif type(getattr(field, attr))==type({}):
                tmpls.append('%s%s: %s'%(prepend, attr,getattr(field,attr)))
            elif type(getattr(field, attr)) in (type(tuple()), type(list()), ObservableList, ObservableReferenceList):
                if attr == "size" and field.size == self.current_template.size:
                    print "size is root.size"
                    tmpls.append('%ssize: root.size'%prepend)
                    continue
                #Looping and removing bracket
                sub = []
                for item in getattr(field,attr):
                    if isinstance(item, float):
                        sub.append('%.2f'%item)
                    elif isinstance(item, basestring):
                        sub.append('"%s"'%item)
                    else:
                        sub.append(str(item))
                tmpls.append('%s%s: '%(prepend, attr) + ', '.join(sub))
            else:
                tmpls.append('%s%s: %s'%(prepend, attr, getattr(field, attr)))
        if isinstance(field, LinkedField):
            for child_field in field.children:
                if hasattr(child_field, 'is_context') and child_field.is_context:
                    continue
                print 'todo: child to process', child_field
        tmpls.append('')

    def save(self,*args):
        imports = list()
        if not self.current_template.name:
            self.current_template.name = "TMPL"
        tmpls=["<%s@BGTemplate>:"%self.current_template.name]
        from kivy.metrics import cm
        if self.ids.tmpl_unit.text == 'cm':
            #Save the size in cm
            w,h = "cm(%.2f)"%(self.current_template.width/cm(1)), "cm(%.2f)"%(self.current_template.height/cm(1))
        else:
            w,h = self.current_template.size
        tmpls.append('\tsize: %s, %s'%(w,h))
        for node in self.ids.fields.root.nodes:
            field = node.target
            self.export_field(field, tmpls, imports, level=2)
        #Prepend include
        if imports:
            tmpls.insert(0, "")
            for imp in imports:
                tmpls.insert(0,"#:include %s"%imp)
        from os import linesep
        kv = linesep.join(tmpls)
        file('Templates/%s.kv'%self.current_template.name,'wb').write(kv)
        templateList.register(BGTemplate.FromText(kv))
        from conf import alert
        alert('Template %s saved'%self.current_template.name)
        #Force update on deck widget
        from kivy.app import App
        deck = App.get_running_app().root.ids.deck
        if deck.ids.tmpl_tree.current_tmpl_name == self.current_template.name:
            deck.update_tmpl(self.current_template.name)

    def on_selection(self, instance, selection):
        tasks = self.ids.tasks
        tasks.clear_widgets()
        if self.selection:
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
            label = Label(text=text, size_hint_x=None, width = 100)
            tasks.add_widget(label)

            ftb = Factory.get('FieldTaskButton')
            data=[
                #(self.expand_selection, 'img/expand2.png'),
                #(self.center_selection, 'img/center.png'),
                (self.center_vertical_selection, 'img/btn_center_vertical.png'),
                (self.center_horizontal_selection,'img/btn_center_horizontal.png'),
                (self.maximize_height, 'img/maximize_height.png'),
                (self.maximize_width, 'img/maximize_width.png'),
                (self.remove_selection, 'img/DeleteRed.png'),
                (self.duplicate_selection, 'img/duplicate.png'),
            ]
            for cb, img in data:
                _button = ftb()
                _button.source = img
                _button.bind(on_press=cb)
                _button.designer = self
                tasks.add_widget(_button)
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
            if len(self.selection)>1:
                #Add alignement button
                pass

    def expand_selection(self,*args):
        if self.selection:
            unit= self.selection[0]
            unit.size = unit.parent.size
            unit.pos = unit.parent.pos

    def maximize_height(self,*args):
        if self.selection:
            unit= self.selection[0]
            unit.height= unit.parent.height
            unit.y= unit.parent.y

    def maximize_width(self,*args):
        if self.selection:
            unit= self.selection[0]
            unit.width= unit.parent.width
            unit.x = unit.parent.x

    def center_selection(self,*args):
        if self.selection:
            unit= self.selection[0]
            unit.center = unit.parent.center

    def center_horizontal_selection(self, *args):
        if self.selection:
            unit = self.selection[0]
            unit.center_x = unit.parent.center_x

    def center_vertical_selection(self, *args):
        if self.selection:
            unit = self.selection[0]
            unit.center_y = unit.parent.center_y

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

#Need to put it at the end because klass needed in kv
Builder.load_file('kv/designer.kv')
