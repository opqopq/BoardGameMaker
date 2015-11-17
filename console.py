__author__ = 'opq'

from kivy.properties import BooleanProperty
from kivy.uix.treeview import TreeView, TreeViewLabel

from kivy.lang import Builder
Builder.load_file('kv/scripts.kv')
Builder.load_file('kv/console.kv')

from kivy.uix.boxlayout import BoxLayout
from kivy.factory import Factory

class BGConsole(BoxLayout):

    def add(self, text, stack=None):
        cl = Factory.Repl_line()
        print text, type(text)
        cl.text =unicode(text)
        self.add_widget(cl)
        #if stack:
        #    tl.is_leaf = False
        #    self.add_node(TreeViewLabel(text=str(stack)), tl)