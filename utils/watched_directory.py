__author__ = 'HO.OPOYEN'


from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.properties import StringProperty, BooleanProperty, ListProperty

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FSWatcherBehavior(object):
    """File System Watcher behavior.

    :Events:
        `on_operations`
            Fired when there is any event on watched dir/file.
    """

    operations = ListProperty(None)
    '''Contains the list of operations/event on wateched folder.
    '''

    path= StringProperty()
    "Watched Path"

    def __init__(self, **kwargs):
        super(FSWatcherBehavior, self).__init__(**kwargs)
        #Now, bind yourseilf on list of templates
        self._observer = Observer()
        self._event_handler = MyFileEventHandler(self)

    def on_path(self, *args):
        self._observer.schedule(self._event_handler, self.path)
        self._observer.start()
        print 'Start Watching'

class WatchedFolderTree(TreeView):
    path = StringProperty()
    updated = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        TreeView.__init__(self, *args, **kwargs)
        #Now, bind yourseilf on list of templates
        self.observer = Observer()
        self.event_handler = MyFileEventHandler(self)

    def on_path(self, *args):
        self.rebuilt()
        self.observer.schedule(self.event_handler, self.path)
        self.observer.start()
        print 'starting', self.updated

    def rebuilt(self):
        print 'rebuilt called', self.updated
        self.clear_widgets()
        self.root.nodes = []
        print "Nodes:", self.root.nodes
        from os import listdir
        for f in listdir(self.path):
            self.add_node(TreeViewLabel(text=f, color_selected=(.6,.6,.6,.8)))

    def on_updated(self, *args):
        print 'on updated', args
        if self.updated:
            self.updated = False
            self.rebuilt()

class MyFileEventHandler(FileSystemEventHandler):
    def __init__(self, target):
        self.target = target
        FileSystemEventHandler.__init__(self)

    def on_any_event(self, event):
        #print event
        #print self.target, self.target.updated
        self.target.operations.append(event)

if __name__ == "__main__":
    path = "templates/"
    from kivy.base import runTouchApp
    runTouchApp(WatchedFolderTree(path = path))