# __author__ = 'MRS.OPOYEN'

import kivy.clock
kivy.clock.Clock.max_iteration = 20
from kivy.lang import Builder
from template import templateList
# #Now the GUI parts of the template
from kivy.properties import ObjectProperty,  DictProperty, StringProperty
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