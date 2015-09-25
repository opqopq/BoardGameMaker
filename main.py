'Main Entry point for new KIVY bassed BGM'

todos= [
    "P3: comprendre pourquoi les cm n'en sont point",
    'P3: change virtual screen stack',
    "P3: bgg browser v2 - file & links",
    "p2: how to have, in designer a way to edit intelligent code, like python sentence ?"
    "P2: still some error in picture memory geneation: no way to be sure it works",
    "P3: do some advancement /progress stuff to help waiting for the ethingy like PDF gen",
   'find a wy to indicate error when loading a non existing file/image, like in image choiceeditor',
    'import template field in template - almost, except for values in valuetree',
    "create a metaclass for field that will triger the agrfegation of attrs into params. this will make life easier/faster for field creation",
    'for field d&d/move, apply rotation effect to angle when calcultaing the drama',
    "bug: Mac OSX: when scatter ruled in designer is added a field and the field is move, it crahs",
]

for i,todo in enumerate(todos):
    print i, todo

from kivy.logger import Logger
Logger.setLevel('WARNING')

##############################################
from kivy.lang import Builder
Builder.load_file('kv/bgm.kv')
##############################################
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
class RootWidget(BoxLayout):

    screen_name = StringProperty('Deck')

    def on_screen_name(self, instance, name, set_screen=True):
        if not name in [s.name for s in self.ids.content.content]:
            if name == 'Browser':
                from geekbrowser import BGGeekBrowser
                self.ids['browser'] = last = BGGeekBrowser(name=name)
            # elif name == 'PrintPreview':
            #     from printer import BGPrinter
            #     self.ids['printer'] = last = BGPrinter(name=name)
            # elif name == 'Layout':
            #     from layout import BGLayoutMaker
            #     self.ids['layout'] = last = BGLayoutMaker(name=name)
#            elif name == 'Console':
#                from console import BGConsole
#                self.ids['bgconsole'] = last = BGConsole(name=name, updated=False)
#            elif name == 'Script':
#                from scripts import BGScriptEditor
#                self.ids['bgscript'] = last = BGScriptEditor(name=name, env=self)
            elif name == 'Designer':
                from designer import BGDesigner
                self.ids['designer'] = last = BGDesigner(name=name)
            elif name =='Settings':
                from conf import CreateConfigPanel
                self.ids['settings'] = last = CreateConfigPanel()
            else:
                raise ValueError('No screen named %s' % name)
            self.ids.content.add_widget(last, name)
            last.name = name
        if set_screen:
            self.ids.content.set_screen(name)

    def log(self, text, stack=None):
        if not 'bgconsol' in self.ids:
            try:
                self.on_screen_name(self, 'Console', False)
            except ValueError:
                print 'Console/Log Screen disabled: resorting to print: ',
                print text, stack
                return
        if not stack:
            import traceback
            stack = traceback.format_exc()
        self.ids.bgconsole.add(text, stack)

from kivy.app import App

class BGMApp(App):
    title = "Kivy Board Game Maker"

    def build(self):
        root =  RootWidget()
        from conf import gamepath
        #root.ids['deck'].file_chooser.load_folder(gamepath)
        return root

    def alert(self, text="", status_color=(0, 0, 0, 1), keep = False):
        button = self.root.ids.message
        bar = self.root.ids.message_bar
        bar.background_color = status_color
        button.text = str(text)
        if not keep:
            from kivy.clock import Clock
            def cb(*args):
                self.alert(keep = True)
            Clock.schedule_once(cb, 2)

    def set_screen(self, screen_name):
        self.root.ids.screen_spinner.text = screen_name

    def compute_stats(self,grid):
        return self.root.ids['deck'].compute_stats(grid)

if __name__ == '__main__':
    BGMApp().run()
