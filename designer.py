__author__ = 'HO.OPOYEN'

from kivy.lang import Builder
from kivy.uix.scatterlayout import ScatterLayout
from kivy.graphics import Color, Line
from kivy.metrics import cm
from kivy.uix.treeview import TreeViewLabel, TreeViewNode
from kivy.properties import ListProperty, DictProperty, ObservableList, ObservableReferenceList, ObservableDict
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from fields import BaseField
from template import BGTemplate, templateList
from deck import TreeViewField
from os.path import isfile
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.treeview import TreeView
from kivy.uix.relativelayout import RelativeLayout


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

    def on_touch_up(self, touch):
        #clear only if we clicked in the stencil view
        CLEAR = self.parent.collide_point(*touch.pos)
        for widget in self.designer.current_template.children:
            if widget.collide_point(*widget.parent.to_widget(*touch.pos)):
                CLEAR = False
        if CLEAR:
                self.designer.selections = dict()
                self.designer.last_selected = None
        return ScatterLayout.on_touch_up(self, touch)


class TreeFieldEntry(TreeViewNode, BoxLayout):
    target = ObjectProperty(None)
    designer = ObjectProperty()


class TreeTmplFieldEntry(TreeViewNode, BoxLayout):
    target = ObjectProperty(None)
    designer = ObjectProperty()


class TmplChoicePopup(Popup):
    cb = ObjectProperty()


class BGDesigner(FloatLayout):
    current_template = ObjectProperty(None, rebind=True)
    selections = DictProperty(rebind=True)
    last_selected = ObjectProperty(rebind = True, allownone = True)
    nodes = DictProperty()
    #Place Holder when copying size/pos of a widget
    _do_copy = None
    #String for holding the path at which template will be saved in the form name@path
    tmplPath = StringProperty()

    templates = ListProperty()

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
                if "skip_designer" in fieldDict[key].__dict__ and fieldDict[key].skip_designer:#test of __dict__ ensure existencfe at the calss level,, not in its basis
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
        self.new()
        Clock.schedule_once(build)
        self.params_cache = dict()

    def add_template_field(self):
        from kivy.core.window import Window
        cp_width = min(Window.size)*.8
        cp_pos = [(Window.size[0]-cp_width)/2,(Window.size[1]-cp_width)/2]
        from editors import TemplateFileEditorPopup
        tcp = TemplateFileEditorPopup(pos=cp_pos, size=(cp_width, cp_width))
        tcp.name =' New Template Field'
        def cb(instance):
            s = instance.ids.fpicker.selection
            val = instance.ids.tmpl_name.text
            if len(s) and isfile(s[0]):
                _name = val
                if val == '-':
                    _name = ''
                tmplname = '%s@%s'%(_name, s[0])
                from template import BGTemplate
                print '[Designer] Add Template within template'
                tmpl = BGTemplate.FromFile(tmplname).pop()
                node = self.insert_field(tmpl)
                self.selections = {tmpl: None}
                self.last_selected = tmpl

            else:
                from utils import alert
                alert('Wrong selection in template:' + s)
        tcp.cb = cb
        tcp.open()

    def add_field(self, field):
        from fields import fieldDict
        klass = fieldDict.get(field.text, None)
        target = klass(size=(100,100))

        self.current_template.add_widget(target)
        self.insert_field(target)
        #Select the new field on only this

        self.selections = {target: None}
        self.last_selected = target

    def insert_field(self, target, parent=None, is_root=False):
        #Make Them designer still
        if not is_root:
            target.designed = True
        target.designer = self
        target.template = self.current_template
        if parent is None:
            #print 'nodes is', self.nodes, id(self.current_template), [id(x) for x in self.nodes.keys()]
            parent = self.nodes[self.current_template]
        child = self.ids.fields.add_node(TreeFieldEntry(target=target, designer=self), parent)
        self.nodes[target] = child
        #Way to come back
        child.target = target
        return child

    def display_field_attributes(self, target, force_refresh=False):
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

        if target in self.params_cache and not force_refresh:
            params.root.nodes = self.params_cache[target]
            params._trigger_layout()
            return

        SKIP_TMPL_POS = target == self.current_template
        SKIP_LIST = ['x','y','z','pos_hint','size_hint', 'angle','editable', 'printed', 'name']
        for subNodeName in target.menu:
            subNode = self.ids.params.add_node(TreeViewLabel(text=subNodeName))
            for attr in target.menu[subNodeName]:
                #Complete hack for root not
                if SKIP_TMPL_POS and attr in SKIP_LIST: continue
                self.ids.params.add_node(TreeViewField(name=attr, editor=target.params[attr](target),size_hint_y= None, height=30), subNode)
                nodes_done.add(attr)
        #Style Node
        self.insert_styles(target)
        #Now for the attributes without menu
        for attr in target.params:
            if attr in nodes_done: continue
            if SKIP_TMPL_POS and attr in SKIP_LIST: continue
            self.ids.params.add_node(TreeViewField(name=attr, editor=target.params[attr](target),size_hint_y= None, height=30))
        #Special case for template: display specific children attribute
        if isinstance(target, BGTemplate) and target != self.current_template:
            tmpl = target
            node = self.ids.params.add_node(TreeViewLabel(text=tmpl.template_name, color_selected=(.6, .6, .6, .8)))
            node.is_leaf = False #add the thingy
            #point to the template
            node.template = tmpl
            #Deal with Template Properties:
            for pname, editor in tmpl.vars.items():
                self.ids.params.add_node(TreeViewField(name=pname, editor=editor(tmpl)), node)
            #Deal with KV style elemebts
            for fname in tmpl.ids.keys():
                if not isinstance(tmpl.ids[fname], BaseField):
                    continue
                _wid = tmpl.ids[fname]
                if not _wid.editable:
                    continue
                if _wid.default_attr:
                    w = _wid.params[_wid.default_attr](_wid)
                    if w is not None:#None when not editable
                        self.ids.params.add_node(TreeViewField(pre_label=fname, name=_wid.default_attr, editor=w), node)

        self.params_cache[target] = params.root.nodes[:]

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

    def on_current_template(self, instance, value):
        if value:
            self.ids.content.clear_widgets()
            self.ids.content.add_widget(value)

    def load(self, templateName):
        #First clean a little
        self.clear()
        if '@' in templateName:
            #load from file:
            from template import BGTemplate
            tmpls = BGTemplate.FromFile(templateName)
        else:
            tmpls= [templateList[templateName]]
        self.tmplPath = templateName
        for template in tmpls:
            print 'adding template', template, template.name, template.template_name
            self.add_template(template)

    def add_template(self, tmpl=None):
        if tmpl is None:
            tmpl = BGTemplate()
            tmpl.template_name = 'Tmpl%d'%(len(self.templates)+1)
        self.templates.append(tmpl)
        tmpl_node = self.ids.fields.add_node(TreeTmplFieldEntry(target=tmpl, designer=self))
        self.nodes[tmpl] = tmpl_node
        #This add the tmpl to content
        self.current_template = tmpl
        #Have to do that, as chilndre is in the wrong way  !
        ordered_child = [c for c in tmpl.children if isinstance(c, BaseField)]
        ordered_child.sort(key=lambda x: x.z)
        self.ids.fields.toggle_node(tmpl_node)
        for target in ordered_child:
            self.insert_field(target, parent=tmpl_node)

    def clear(self):
        self.templates = list()
        for nodeIndex, node in self.nodes.items():
            self.ids.fields.remove_node(node)
        self.ids.content.clear_widgets()
        self.nodes = dict()

    def new(self, *args):
        self.clear()
        tmpl = BGTemplate()
        tmpl.template_name = 'NewTemplate'
        self.add_template(tmpl)

    def save(self,PATH=None, *args):
        from conf import CP
        from os.path import isfile, split, splitext
        if PATH is not None:
            self.current_template.template_name = splitext(split(PATH)[-1])[0].capitalize()
            self.tmplPath = PATH
        else:
            self.current_template.template_name = self.current_template.template_name.capitalize()
        if PATH is None:
            if self.tmplPath:
                PATH = self.tmplPath
                if "@" in PATH:
                    PATH = PATH.split('@')[-1]
                overwrite = True
            else:
                PATH = 'templates/%s.kv'%self.current_template.template_name
                overwrite = CP.getboolean('Designer','OVERWRITE_SAVED_TMPL')
                alert('Template Saved in Library as %s.kv'%self.current_template.template_name)
        else:
            overwrite = CP.getboolean('Designer', 'OVERWRITE_SAVED_TMPL')
        exists = isfile(PATH)
        kv = self.export_kv(split(PATH)[0])
        if overwrite or not exists:
            file(PATH,'wb').write(kv)
        else:
            from utils import alert
            alert('Template %s already exists !'%PATH)
            return
        from utils import alert
        alert('Template %s saved'%self.current_template.template_name)
        #Force update on deck widget
        from kivy.app import App
        deck = App.get_running_app().root.ids.deck
        stack = deck.ids['stack']
        from template import find_template_path, templateList
        templateList.register_file(PATH)
        for child in stack.children:
            if not hasattr(child, 'template'): continue
            _, tpath = find_template_path(getattr(child, 'template'))
            if tpath.endswith(PATH):
                child.realise(use_cache=True)
        print 'todo: how do I save pultiple template on a single KV file ? '

    def export_kv(self, PATH=None):
        if PATH is None:
            from conf import gamepath
            PATH = gamepath
        from kivy.logger import Logger
        #print " -- EXPORT KV  -- "*10
        from conf import CP
        relativ = CP.getboolean('Designer', 'TMPL_RELATIVE_SIZE_POS')
        save_cm = CP.getboolean('Designer', 'SAVE_IN_CM')
        save_relpath = CP.getboolean('Designer', 'TMPL_RELATIVE_GAMEPATH')
        imports = list()
        directives = self.current_template.directives[:]
        #Will be used to find a interresting base for relpath
        print 'at this stage, i should insert a check for name vs libraty & templates'
        if not self.current_template.template_name:
            print 'Current template as no name: reverting to default'
            self.current_template.template_name = "TMPL"
        KV = list()
        for template in self.templates:
            tmpls, imports, directives = template.export_to_kv(level=1, save_cm=save_cm, relativ=relativ, save_relpath=save_relpath, RELPATH=PATH)
            Logger.debug('export these imports to kv: ' + str(imports))
            print self.nodes, template
            for node in self.nodes[template].nodes:
                if not hasattr(node, 'target'):
                    continue
                field = node.target
                if field == template: #skip export of the root template: done above
                    continue
                t, i, d = field.export_field(level=2, save_cm=save_cm, relativ=relativ, save_relpath=save_relpath, RELPATH=PATH)
                tmpls.extend(t)
                imports.extend(i)
                directives.extend(d)
            #Prepend include
            if imports:
                tmpls.insert(0, "")
                for imp in imports:
                    if imp:
                        tmpls.insert(0,"#:include %s"%imp)
            Logger.debug("directives at the end" + str(directives))
            if directives:
                tmpls.insert(0,"")
                for directive in directives:
                    tmpls.insert(0, "#:%s"%directive)

            from os import linesep
            KV.append(linesep.join(tmpls))
            KV.extend('  ')
        return linesep.join(KV)

    def on_last_selected(self, instance, field):
        tasks = self.ids.tasks
        tasks.clear_widgets()
        #Just make sure that the dos are aligned on the widget
        children = self.current_template.children
        for widget in children:
            widget.selected = widget in self.selections
        if field:
            if field in self.templates:
                self.current_template = field
            else:
                self.current_template = field.parent
                #Re add to make it at the top
                _p = field.parent
                _p.remove_widget(field)
                _p.add_widget(field)
            #Add some button around me
            from kivy.factory import Factory
            from kivy.uix.label import Label
            #Now for the big show
            text = field.name if field.name else field.Type
            from utils.fontello import FontIcon
            icon = FontIcon(icon=text, color=(0,0,0,1), font_size=24, size_hint_x=None, width=40)
            tasks.add_widget(icon)
            if text.lower().endswith('field'):
                text=text[:-5]
            label = Label(text=text, size_hint_x=None, width=100)
            tasks.add_widget(label)

            #Skip this if targetting current template
            if field != self.current_template:
                ftb = Factory.get('FieldTaskButton')
                data = [
                    (self.remove_selection, 'cancel'),
                    (self.duplicate_selection, 'duplicate'),
                ]
                for cb, img in data:
                    _button = ftb()
                    #_button.source = img
                    _button.icon = img
                    _button.bind(on_press=cb)
                    _button.designer = self
                    tasks.add_widget(_button)
                ##self.insertMoveUpDownButton()
                PIMGS = Factory.get('PositionImageSpinner')
                SIMGS = Factory.get('SizeImageSpinner')
                img_spinner = PIMGS()
                img_spinner.bind(text=self.position_selection)
                tasks.add_widget(img_spinner)
                img_spinner = SIMGS()
                img_spinner.bind(text = self.align_selection)
                tasks.add_widget(img_spinner)
                #Now load the specific attributes matrix/tree for field 6> activated by a double tap on the field
                ##self.display_field_attributes(field)
                self.ids.fields.select_node(self.nodes[field])

    def position_selection(self, *args):
        pos= args[1]
        conv ={'Left': 'x', 'Bottom': 'y', 'Cent H': 'center_x', 'Cent V': 'center_y'}
        attr = conv.get(pos, pos.lower())
        if self.selections:
            unit = self.last_selected
            setattr(unit, attr, getattr(unit.parent,attr))

    def align_selection(self, *args):
        pos = args[1]
        if self.selections:
            unit = self.last_selected
            if pos == 'Max H':
                unit.width = unit.parent.width
                unit.x = unit.parent.x
            elif pos == 'Max V':
                unit.height= unit.parent.height
                unit.y= unit.parent.y
            elif pos == 'Copy':
                from utils import alert
                alert('Choose target to copy size from')
                self._do_copy =('size', unit)

    def duplicate_selection(self, *args):
        if self.selections:
            unit= self.last_selected
            copy = unit.Copy()
            unit.parent.add_widget(copy)
            self.insert_field(copy)
            #Select the new field
            self.selections = dict()
            self.selections[copy] = None
            self.last_selected = copy

    def remove_selection(self,*args):
        if self.selections:
            unit = self.last_selected
            parent = unit.parent
            parent.remove_widget(unit)
            self.ids.fields.remove_node(self.nodes[unit])
            #Also tell the properties tree to update
            params = self.ids.params
            params.current_field == None
            params.clear_widgets()
            params.nodes = dict()
            params.root.nodes = [] # as clear widgets does not works
            params.root.text = ""
            #unselect all ?
            self.selections = dict()
            self.last_selected = None

    def write_file_popup(self,title,cb, default='TMPL.kv'):
        from kivy.factory import Factory
        p = Factory.get('WriteFilePopup')()
        p.title = title
        p.cb = cb
        p.default_name = default
        p.open()

    def align_group(self, way):
        if way.startswith('center'):
            mz = min([getattr(o, way[-1]) for o in self.selections])
            Mz = max([getattr(o, way[-1]) for o in self.selections])
            basis = int(mz + (Mz-mz)/2)
            for s in self.selections:
                setattr(s, way[-1], basis)
        else:
            if way in ['x','y']:
                op = min
            else:
                op = max
            basis = op([getattr(o, way) for o in self.selections])
            for s in self.selections:
                setattr(s, way, basis)

    def resize_group(self, dim):
        order = max
        if dim.startswith('-'):
            dim = dim[1:]
            order = min
        basis = order([getattr(c, dim) for c in self.selections])
        for c in self.selections:
            setattr(c, dim, basis)

    def distribute_group(self, dim):
        if len(self.selections) < 3:
            return
        sorted_phs = sorted(self.selections, key=lambda x: getattr(x, dim))
        m, M = getattr(sorted_phs[0], dim), getattr(sorted_phs[-1], dim)
        step = (M-m)/(len(self.selections) - 1)
        for i, c in enumerate(sorted_phs):
            setattr(c, dim, m+i*step)

    def stick_group(self, way):
        sorted_fields = sorted(self.selections, key= lambda x:getattr(x, way))
        others = dict(x='right',y='top', top='y',right='x')
        if way in ('top','right'):
            sorted_fields.reverse()
        former = None
        while sorted_fields:
            base = sorted_fields.pop(0)
            if former:
                setattr(base,way,getattr(former, others[way]))
            former = base

class FieldTreeView(TreeView):
    def on_selected_node(self, instance, selected_node):
        if selected_node:
            if hasattr(selected_node,'target'):
                self.designer.selections[selected_node.target] = None
                self.designer.last_selected = selected_node.target
                self.designer.display_field_attributes(selected_node.target)
                if selected_node.target in self.designer.templates:
                    self.designer.current_template = selected_node.target
                else:
                    self.designer.current_template = selected_node.target.parent
                # somz add/remove to change layout
                ##parent = selected_node.target.parent
                ##parent.remove_widget(selected_node.target)
                ##parent.add_widget(selected_node.target)

            else:# root is selected: get the info of the tempalte
                #self.designer.selections = [self.designer.current_template]
                self.designer.selections = dict()
                self.designer.last_selected = None
                if selected_node.target in self.designer.templates:
                    self.designer.display_field_attributes(selected_node.target)
                    self.designer.current_template = selected_node.target
                else:
                    self.designer.current_template = selected_node.target.parent


#Need to put it at the end because klass needed in kv
Builder.load_file('kv/designer.kv')
