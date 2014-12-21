__author__ = 'opq'

from kivy.properties import BooleanProperty
from kivy.uix.treeview import TreeView, TreeViewLabel

class BGConsole(TreeView):
    updated = BooleanProperty(False)

    def add(self, text, stack=None):
        tl = TreeViewLabel(text = str(text))
        self.add_node(tl)
        if stack:
            tl.is_leaf = False
            self.add_node(TreeViewLabel(text=str(stack)), tl)
        self.updated = True
