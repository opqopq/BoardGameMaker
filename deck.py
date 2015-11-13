# __author__ = 'MRS.OPOYEN'

import kivy.clock
kivy.clock.Clock.max_iteration = 20
from kivy.lang import Builder
# #Now the GUI parts of the template
from kivy.properties import ObjectProperty,  DictProperty, StringProperty
from kivy.uix.treeview import TreeView, TreeViewLabel, TreeViewNode
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

Builder.load_file('kv/deck.kv')


class TreeViewField(TreeViewNode,BoxLayout):
    editor = ObjectProperty(None)
    name = StringProperty("")
    pre_label = StringProperty('')

    def __init__(self, **kwargs):
        TreeViewNode.__init__(self, **kwargs)
        self.size_hint_y = None
        self.height =  35
        #Add Label & target
        from kivy.uix.togglebutton import ToggleButton
        from editors import AdvancedCodeEditor
        bl = BoxLayout(orientation="horizontal")
        self.add_widget(bl)
        if self.pre_label:
            bl.add_widget(Label(size_hint_x=.25, halign='left', shorten=True, text=self.pre_label))
            bl.add_widget(self.editor.create(self.pre_label, self.name,size_hint_x=.75))
        else:
            if 'standard' in kwargs and kwargs['standard']:
                b = Label(size_hint_x=.4, halign='left', shorten=True, text=self.name)
                e = self.editor.create(self.name, self.name,size_hint_x=.75)
                bl.add_widget(b)
                bl.add_widget(e)
            else:
                b = ToggleButton(size_hint_x=.4, halign='left', shorten=True, text=self.name)
                e = self.editor.create(self.name, self.name,size_hint_x=.75)
                t = AdvancedCodeEditor(self.editor.target).create(self.name, self.name, size_hint_x=.75)
                def switch(*args):
                    if e in bl.children:
                        bl.remove_widget(e)
                        bl.add_widget(t)
                        self.editor.target.code_behind[self.name] = t.children[-1].text
                    else:
                        bl.remove_widget(t)
                        bl.add_widget(e)
                        del self.editor.target.code_behind[self.name]
                b.bind(on_press=switch)
                bl.add_widget(b)
                #if code behind, directly switch to advanced editor with proper stuff
                if self.name in self.editor.target.code_behind:
                    bl.add_widget(t)
                    b.state = 'down'
                    self.editor.target.code_behind[self.name] = t.children[-1].text
                else:
                    bl.add_widget(e)

class ScriptNode(TreeViewNode,BoxLayout):
    text = StringProperty('')


class ScriptTree(TreeView):

    def __init__(self, *args, **kwargs):
        TreeView.__init__(self, *args, **kwargs)
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
            node = self.add_node(ScriptNode(text=script, color_selected=(.6,.6,.6,.8)))
            node.is_leaf = not(bool(scriptList[script].vars))#add the thingy
            #point to the template
            node.script= scriptList[script]
            self.nodes[script] = node

    def node_loader(self, treeview, node):
        if node and hasattr(node, 'script'):
            self.select_node(node)
            script = node.script
            #Deal with Template Properties:
            for pname, editor in script.vars.items():
                self.add_node(TreeViewField(name=pname, editor=editor(script), standard=True), node)
            if not node.nodes:
                node.is_leaf = True