# __author__ = 'MRS.OPOYEN'

import kivy.clock
kivy.clock.Clock.max_iteration = 20

from kivy.lang import Builder
from template import templateList
from kivy.uix.floatlayout import FloatLayout

# #Now the GUI parts of the template
from kivy.properties import ObjectProperty, ListProperty, DictProperty, StringProperty
from models import ImgPack
from kivy.uix.treeview import TreeView, TreeViewLabel, TreeViewNode
from kivy.uix.boxlayout import BoxLayout
from fields import Field

Builder.load_file('kv/deck.kv')

from utils.watched_directory import FSWatcherBehavior

class TreeViewField(TreeViewNode,BoxLayout):
    editor = ObjectProperty(None)
    name = StringProperty("")
    pre_label = StringProperty('')

    def __init__(self, **kwargs):
        TreeViewNode.__init__(self, **kwargs)
        #Add Label & target
        from kivy.uix.label import Label
        from kivy.uix.boxlayout import BoxLayout
        bl = BoxLayout(orientation="horizontal")
        self.add_widget(bl)
        if self.pre_label:
            bl.add_widget(Label(size_hint_x=.25, halign='left', shorten=True, text=self.pre_label))
            bl.add_widget(self.editor.create(self.pre_label, self.name,size_hint_x=.75))
        else:
            bl.add_widget(Label(size_hint_x=.4, halign='left', shorten=True, text=self.name))
            bl.add_widget(self.editor.create(self.name, self.name,size_hint_x=.75))

class TemplateTree(FSWatcherBehavior,TreeView):
    #current_tmpl = ObjectProperty(templateList['Empty'])
    current_tmpl_name = 'Default'
    nodes = DictProperty()

    def __init__(self, *args, **kwargs):
        super(TemplateTree,self).__init__( *args, **kwargs)
        #Now, bind yourseilf on list of templates
        from template import templateList
        templateList.bind(templates=self.Rebuild)
        self.Rebuild()
        #Now add on load
        self.load_func = self.node_loader
        #Start listening on change on Templates dir
        self.path = 'Templates'

    def on_operations(self, instance, operations):
        from template import templateList
        from kivy.logger import Logger
        if operations:
            last_op = operations[-1]
            if not last_op.is_directory and last_op.event_type in('created', 'modified'): #it is a new file !
                if last_op.event_type == 'modified':
                    print 'Watchdog Modify event detected. Skipping it for now'
                    return
                fname = last_op.src_path
                if fname.endswith('.kv'):
                    #Load it !
                    Logger.warn(('Loading detected KF file %s'%fname))
                    templateList.register_file(fname)
            #Reselect current select template
            current_node = self.selected_node
            self.select_node(self.root)
            self.select_node(current_node)

    def Rebuild(self,*args):
        self.clear_widgets()
        self.nodes = dict()
        self.root.nodes = [] # as clear widgets does not works
        from template import templateList
        for tmpl in sorted(templateList.templates):
            node = self.add_node(TreeViewLabel(text=tmpl, color_selected=(.6,.6,.6,.8)))
            node.is_leaf = False #add the thingy
            #point to the template
            node.templateName = tmpl
            self.nodes[tmpl] = node

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.is_double_tap and getattr(touch, 'button', -1) == "left":
            node = self.get_node_at_pos(touch.pos)
            if node and hasattr(node, 'templateName'):
                #Change selection, to trigger an on_select_change event later on
                self.select_node(self.root)
                #Changing the lsit will force re-creation of the tree
                templateList.refresh(self.current_tmpl_name)
                self.select_node(node)
        return TreeView.on_touch_down(self, touch)

    def on_node_expand(self, node):
        self.select_node(node)

    def on_node_collapse(self, node):
        self.select_node(node)

    def node_loader(self, treeview, node):
        if node and hasattr(node, 'templateName'):
            self.select_node(node)
            templateName = node.templateName
            tmpl = templateList[templateName]
            childrens = tmpl.ids.values()

            #Deal with Template Properties:
            for pname, editor in tmpl.vars.items():
                self.add_node(TreeViewField(name=pname, editor=editor(tmpl)), node)
            #Deal with KV style elemebts
            for fname in tmpl.ids.keys():
                if not isinstance(tmpl.ids[fname], Field):
                    continue
                if not tmpl.ids[fname].editable:
                    continue
                _wid = tmpl.ids[fname]
                if not _wid.editable:
                    continue
                if _wid.default_attr:
                    w = _wid.params[_wid.default_attr](_wid)
                    if w is not None:#None when not editable
                        self.add_node(TreeViewField(pre_label=fname, name=_wid.default_attr, editor=w), node)
            #Now for the other ones....
            from kivy.logger import Logger
            Logger.info("Skipping item without ID: their params can not be saved to ImgPack'")
            if 0:
                for field in tmpl.children:
                    if field in childrens:
                        continue
                    if getattr(field, 'is_context', False):
                        continue
                    #Skip unamed or unwanted field
                    if not field.editable:
                        continue
                    if field.default_attr:
                        w = field.params[field.default_attr](field)
                        if w is not None:#None when not editable
                            pre_label = field.name or field.id or field.Type
                            self.add_node(TreeViewField(pre_label=pre_label, name = field.default_attr, editor=w), node)
            if not node.nodes:
                node.is_leaf = True

class ScriptTree(TemplateTree):

    def __init__(self, *args, **kwargs):
        TreeView.__init__(self, *args, **kwargs)
        #Now, bind yourseilf on list of templates
        #Now, bind yourseilf on list of templates
        from scripts import scriptList
        scriptList.bind(scripts=self.Rebuild)
        self.Rebuild()
        #Now add on load
        self.load_func = self.node_loader

    def Rebuild(self,*args):
        self.clear_widgets()
        self.nodes = dict()
        self.root.nodes = [] # as clear widgets does not works

        from scripts import scriptList
        for script in sorted(scriptList.scripts):
            node = self.add_node(TreeViewLabel(text=script, color_selected=(.6,.6,.6,.8)))
            node.is_leaf = False #add the thingy
            #point to the template
            node.scriptName= script
            self.nodes[script] = node

    def node_loader(self, treeview, node):
        from scripts import scriptList
        if node and hasattr(node, 'scriptName'):
            self.select_node(node)
            scriptName= node.scriptName
            script = scriptList[scriptName]
            #Deal with Template Properties:
            for pname, editor in script.vars.items():
                self.add_node(TreeViewField(name=pname, editor=editor(script)), node)
            if not node.nodes:
                node.is_leaf = True

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.is_double_tap and getattr(touch, 'button', -1) == "left":
            from scripts import scriptList
            node = self.get_node_at_pos(touch.pos)
            if node and hasattr(node, 'scriptName'):
                script = scriptList[node.scriptName]
                print 'executing', node.scriptName,
                script.execute()
                print 'done'

        return TreeView.on_touch_down(self, touch)

from kivy.uix.treeview import TreeView
class BGDeckMaker(FloatLayout):
    stack = ListProperty([])

    def delete_pack(self):
        #Find the current selected pack
        current_node = self.ids.stackview.selected_node
        if not current_node:
            from conf import alert
            alert('Select a pack first in Stack Tab')
            return
        self.stack.remove(current_node.pack)

    def new_stack(self):
        self.stack = []

    def add_pack(self):
        tmpl = templateList[self.ids.tmpl_tree.current_tmpl_name]
        #Here is hould loop on the template to apply them on values
        values = dict()
        node = self.ids.tmpl_tree.nodes[tmpl.name]
        for child_node in node.nodes:
            for child in child_node.walk(restrict=True):
                key = getattr(child, 'target_key','')
                sv = getattr(child, 'stored_value','')
                if key and sv: # means somthing has changed
                    if child.target_attr in tmpl.vars: #just a tmpl variable
                        values[key] = sv
                    else:
                         values["%s.%s"%(child.target_attr, key)] = sv
        src = self.ids['file_chooser']
        if src.selection:
            values['default.source']=src.selection[0]
        pack = ImgPack(tmpl, int(self.ids['qt'].text), self.ids['dual'].active, values)
        self.stack.append(pack)
        #Add it the the printpreview
        from kivy.app import App
        App.get_running_app().root.layout(self.stack)

    def on_stack(self, instance, stack):
        from kivy.factory import Factory
        IntNode = Factory.get('IntNode')
        BoolNode = Factory.get('BoolNode')
        #first empty the list
        tree = self.ids.stackview
        tree.clear_widgets()
        tree.nodes = dict()
        tree.root.nodes = [] # as clear widgets does not works
        for pindex, pack in enumerate(stack):
            node = self.ids.stackview.add_node(TreeViewLabel(text="%d: %s"%(pindex,str(pack))))
            node.values = pack.values
            node.template = pack.template
            node.pack = pack
            qt = IntNode()
            def cb(val):
                try:
                    pack.size = int(val)
                    node.text = str(pack)
                except ValueError, E:
                    from conf import alert
                    alert(E)
            qt.callback = cb
            qt.ids.value.text = str(pack.size)
            self.ids.stackview.add_node(qt, node)
            dualNode = BoolNode()
            def dcb(active):
                try:
                    pack.dual = bool(active)
                    node.text = str(pack)
                except ValueError, E:
                    from conf import alert
                    alert(E)
            dualNode.callback = dcb
            dualNode.ids.value.active = pack.dual
            self.ids.stackview.add_node(dualNode, node)

    def update_display(self):
        """Update the scatter to current template"""
        tmpl = templateList[self.ids.tmpl_tree.current_tmpl_name]
        scatter = self.ids['image']
        scatter.clear_widgets()
        scatter.add_widget(tmpl)
        scatter.size = tmpl.size

    def set_display(self, node):
        if not hasattr(node, 'template'):
            return
        tmpl, values = node.template, node.values
        template = tmpl.blank()
        template.apply_values(values)
        scatter = self.ids['image']
        scatter.clear_widgets()
        scatter.add_widget(template)
        scatter.size = template.size

    def update_image(self, filename):
        """for a given template, update its default imgefield to the current file selection value"""
        from os.path import isdir
        if isdir(filename):
            #schedule callback
            from kivy.clock import Clock
            from conf import wait_cursor
            from functools import partial
            wait_cursor(True)
            Clock.schedule_once(partial(self.create_folder_view, filename),0)
            return
        from fields import ImageField
        tmpl = templateList[self.ids.tmpl_tree.current_tmpl_name]
        if tmpl:
            #Now acocuting for named children, in klass mode
            for child in tmpl.children:
                if child.id == 'default' and isinstance(child, ImageField):
                    child.source = filename
            #Same stuff, for ids mode, in KV mode
            for cname in tmpl.ids.keys():
                child = tmpl.ids[cname]
                if cname == "default" and isinstance(child, ImageField):
                    child.source = filename
        self.update_display()

    def create_folder_view(self, filename, dt):
        from kivy.uix.stacklayout import StackLayout
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.image import Image
        from utils.hoverable import HoverBehavior
        scatter = self.ids.image
        scatter.clear_widgets()
        scatter.size = scatter.parent.width - self.ids.options.width - 60, scatter.parent.height
        scatter.pos = self.ids.options.right + 5, 0
        sc = ScrollView(size=scatter.size)
        sl = StackLayout(orientation='lr-tb', size = scatter.size, padding = 20, spacing=10, size_hint_y=None)
        sl.bind(minimum_height=sl.setter('height'))
        sc.add_widget(sl)
        scatter.add_widget(sc)
        from glob import glob
        from os.path import join
        from kivy.properties import StringProperty
        from conf import alert
        class HImage(HoverBehavior, Image):
            text= StringProperty()

            def on_enter(self):
                alert(self.text, keep=True)

            def on_leave(self):
                alert("")

        names = list()
        for pattern in ['*.jpg','*.jpeg','*.png','*.bmp','*.gif']:
            names.extend(glob(join(filename,pattern)))
        for imgname in sorted(names):
            sl.add_widget(HImage(source=imgname, size_hint=(None,None), size=(100,100), text= imgname))
        from conf import wait_cursor
        wait_cursor(False)

    def update_tmpl(self, tmplName):
        """On tmplate change, ensure the current select image is copied to the default imagefield of the new tmplate"""
        self.ids.tmpl_tree.current_tmpl_name = tmplName
        #Now copy current image selection, if any
        file_chooser = self.ids['file_chooser']
        if file_chooser.selection:
            self.update_image(file_chooser.selection[0])
        else:
            self.update_display()

    def export_stack(self):
        from conf import wait_cursor,log, alert
        wait_cursor()
        try:
            from kivy.app import App
            root = App.get_running_app().root
            #Ensure screeen is present
            root.on_screen_name(self, 'PrintPreview', False)
            root.ids.printer.ids.book.export_imgs(self.stack)
        except Exception,e:
            import traceback
            log(e, traceback.format_exc())
            alert(e,[1,0,0,1], True)
        wait_cursor()

    def save_stack(self):
        from conf import wait_cursor, log, alert
        wait_cursor()
        try:
            from models import Stack
            s= Stack(name = "Current",path="")
            for imgPack in self.stack:
                s.items.append(imgPack)
            s.saveas("stack.csv")
        except Exception,e:
            log(e)
        wait_cursor()

    def load_stack(self):
        from conf import wait_cursor, log, alert
        wait_cursor()
        try:
            from models import Stack
            s = Stack.from_file("stack.csv")
            for item in s.items:
                self.stack.append(item)
        except Exception, e:
            log(e)
        wait_cursor()
        alert('Stack loaded', status_color=(0,1,0,1))

    def update_card_format(self):
        unit = self.ids.unit.text
        from conf import card_format
        from kivy.metrics import cm
        try:
            w,h= float(self.ids.cw.text), float(self.ids.ch.text)
        except Exception,E:
            from conf import log
            log(E)
            return
        if unit == "cm":
            w *= cm(1)
            h *= cm(1)
        card_format.width, card_format.height = w, h

    def load_folder(self,dirname):
        from os.path import isdir
        if not isdir(dirname):
            return
        print 'Now Load super folder repr wth checkbox'