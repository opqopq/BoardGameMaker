__author__ = 'opq'

from kivy.properties import BooleanProperty
from kivy.uix.treeview import TreeView, TreeViewLabel

from kivy.lang import Builder

Builder.load_file('kv/console.kv')

from kivy.uix.boxlayout import BoxLayout
from kivy.factory import Factory

class BGConsole(BoxLayout):

    def add(self, text, stack=""):
        cl = Factory.Repl_line()
        cl.text =unicode(text)
        cl.stack = stack
        self.add_widget(cl)