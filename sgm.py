import kivy
kivy.require('1.0.8')

from kivy.logger import Logger
Logger.setLevel('WARNING')

from kivy.app import App
from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image, AsyncImage
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.slider import Slider
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, StringProperty, ReferenceListProperty, OptionProperty
from kivy.metrics import cm
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.clock import Clock
from kivy.lang import Builder
from os.path import isdir


Builder.load_file('kv/sgm.kv')
class FolderTreeView(TreeView):
    folder = StringProperty()

    def  load_folder(self, folder):
        self.folder = folder
        from os.path import join, isdir
        from os import listdir
        self.clear_widgets()
        for f in listdir(folder):
            if not isdir(join(folder,f)): continue
            n = self.add_node(TreeViewLabel(text=f))
            n.is_leaf = False
            n.is_loaded = False
            n.path = join(folder, f)

    def callback(self, instance, node):
        from os import listdir
        from os.path import join, isdir
        for f in listdir(node.path):
            if not isdir(join(node.path,f)):
                continue
            n = self.add_node(TreeViewLabel(text=f), node)
            n.is_leaf = False
            n.is_loaded = False
            n.path = join(node.path, f)

    load_func = callback

Factory.register('FolderTreeView',FolderTreeView)


class CardFormat(EventDispatcher):
    #Card format in PIXELS !!!
    width = NumericProperty(cm(6.5))
    height = NumericProperty(cm(8.8))
    size = ReferenceListProperty(width, height)

    keep_ratio = BooleanProperty(True)
    ratio = NumericProperty(6.5/8.8)


    def updateW(self, W, unit):
        if unit=='px':
            self.width = float(W)
        else:
            self.width = float(W) * cm(1)
        if self.keep_ratio:
            self.height = self.width/self.ratio

    def updateH(self,H, unit):
        if unit=='px':
            self.height = float(H)
        else:
            self.height = float(H) * cm(1)
        if self.keep_ratio:
            self.width = self.height * self.ratio

    def on_keep_ratio(self, instance, keep_ratio):
        if keep_ratio:
            self.ratio = self.width/self.height


card_format = CardFormat()

gamepath = r'C:\Users\mrs.opoyen\OneDrive\Games'

if not isdir(gamepath):
    gamepath = "../../../../OneDrive/Games"

class FoldedTabbedPanel(TabbedPanel):
    folded = BooleanProperty(False)

Factory.register('FoldedTabbedPanel',FoldedTabbedPanel)

import os, os.path

class DynamicQuantity(BoxLayout):
    selected = BooleanProperty()

    def on_selected(self, instance, selected):
        if self.selected:
            label = self.children[0]
            try:
                v = int(label.text)
            except ValueError:
                v = 0
            slider = Slider(min=0, max=100, value = 0, size_hint_y=None, height= 20)
            def v_setter(_i, _v):
                label.text = "%s"%(int(_v))
                self.parent.qt = int(_v)
            slider.bind(value=v_setter)
            self.add_widget(slider)
        else:
            if len(self.children)>2: #not only the 'qt' label & the label itself
                self.remove_widget(self.children[0])

class IconImage(ButtonBehavior, AsyncImage):
    selected = BooleanProperty(False)
    inner_box = ObjectProperty(None)
    folder = StringProperty()
    name = StringProperty()

    def on_press(self):
        if self.last_touch.is_double_tap or self.selected:
            stack = self.get_root_window().ids['stack']
            ##########################################################
            qt = int(self.inner_box.ids['qt'].value)
            verso = self.inner_box.ids['dual'].state
            if self.folder:
                #It is a folder, add all the imge from folder
                for f in os.listdir(self.folder):
                    if f[-4:] in ('.jpg','.jpeg', '.png','.gif','*.kv'):
                        box = StackPart()
                        box.source = os.path.join(self.folder,f)
                        box.qt =qt
                        box.verso = verso
                        if f.endswith('.kv'):
                            box.template = f
                        stack.add_widget(box)
            else:
                box = StackPart()
                box.source = self.source
                box.qt = qt
                box.verso = verso
                stack.add_widget(box)
                if self.name.endswith('.kv'):
                    box.template=self.name
            self.selected= False

        else:
            if self.parent.last_selected:
                self.parent.last_selected.selected = False
            self.selected = True
            self.parent.last_selected = self

    def on_selected(self, target,value):
        if self.selected:
            #Add QT / Dual
            self.inner_box = Factory.get('ChoiceBox')(x=self.x, y=self.y+20)
            self.add_widget(self.inner_box)
        else:
            #Remove QT/Dual
            self.remove_widget(self.inner_box)

class StackPart(ButtonBehavior, BoxLayout):
    selected = BooleanProperty(False)
    row = NumericProperty(0)


    def on_press(self):
        if self.last_touch.is_double_tap :
            self.selected= False
            print 'Edition Mode to be launched ? or a thingy to the left ? '
        else:
            if not self.selected:
                if self.parent.last_selected:
                    self.parent.last_selected.selected = False
                self.selected = True
                self.parent.last_selected = self

    def on_selected(self, instance, selected):
        if self.selected:
            #Add Remove Button
            b = Factory.get('HiddenRemoveButton')(source='img/Delete_icon.png')
            b.bind(on_press = lambda x: self.parent.remove_widget(self))
            self.add_widget(b)
            from kivy.animation import Animation
            anim = Animation(width=100, duration=.1)
            anim.start(b)
            print 'template selected is ', self.template
            if self.template:#it is a template: add edit button
                #be = Factory.get('HiddenRemoveButton')(source='img/edit_stack.png')
                be = Factory.get('HiddenRemoveButton')(source='img/writing_blue.png')
                def inner(*args):
                    p = Factory.get('TemplateEditPopup')()
                    p.name = self.template
                    options = p.ids['options']
                    from kivy.uix.button import Button
                    options.add_widget(Button(text='toto'))
                    p.open()
                be.bind(on_press = inner)
                self.add_widget(be)
                anim = Animation(width=100, duration=.1)
                anim.start(be)
        else:
            self.remove_widget(self.children[0])
            if self.template:
                self.remove_widget(self.children[0])
from kivy.factory import Factory
Factory.register('IconImage',IconImage)

from kivy.uix.boxlayout import BoxLayout

class BGDeckMaker(BoxLayout):
    cancel_load = BooleanProperty()

    def empty_stack(self):
        self.ids['stack'].clear_widgets()

    def prepare_print(self):
        from printer import prepare_pdf
        prepare_pdf(self.ids['stack'], (card_format.width, card_format.height))

    def load_folder(self,folder):
        self.cancel_load = False
        from functools import partial
        if not folder: return
        #FOLD = False
        progress = self.ids['load_progress']
        pictures = self.ids['pictures']
        pictures.clear_widgets()
        C = len( [x for x in os.listdir(folder) if x.endswith(('.jpg','.png','.gif','.kv'))])
        progress.max = C
        progress.value = 1
        pg = Factory.get('PictureGrid')()
        pg.add_widget(IconImage(source='img/AllFolder.png', folder = folder, name="Add %d Imgs"%C))
        def inner(_f,_pictures,_progress, *args):
            if self.cancel_load:
                return False
            #FOLD = True
            if _f.endswith('.kv'): #it is a template:
                source = 'img/card_template.png'
            else:
                source  = os.path.join(folder,_f)
            img = IconImage(source=source, name=_f)
            _pictures.add_widget(img)
            _progress.value += 1
        for index,f in enumerate(os.listdir(folder)):
            if f.endswith(('.jpg','.jpeg', '.png','.gif', '.kv')):
                Clock.schedule_once(partial(inner, f, pg, progress),0+0.001*index)
        def complete(*args):
            print 'done with image. pasting all'
            #have the grid appear in here
            pg_scroll = self.ids['pg_scroll']
            self.ids['pg_scroll'].remove_widget(pictures)
            pg_scroll._viewport = None
            pg_scroll.add_widget(pg)
            self.ids['pictures'] = pg
        Clock.schedule_once(complete, 0.01*(index+1))
        #self.ids['options'].folded = FOLD

    def load_file(self, filepath='deck.json'):
        import json
        od = json.load(file(filepath,'rb'))
        base = od['base']
        print 'stack loaded from base', base
        from os.path import join, isdir
        if not isdir(base):
            print 'Warning, base for path does not exists on this computer', base
        cards = od['cards']
        stack = self.ids['stack']
        for obj in cards:
            qt = int(obj['qt'])
            verso = 'down' if obj['dual'] else 'normal'
            box = StackPart()
            box.source = join(base,obj['source'])
            box.qt = qt
            box.verso = verso
            box.template = obj['template']
            stack.add_widget(box)
        #Load Folder base - might come handy
        if isdir(base):
            self.ids['file_chooser'].path = base

    def export_file(self, filepath='deck.json'):
        from collections import OrderedDict
        import json
        od = OrderedDict()
        cards = list()
        #First, find a common base to all these path
        from os.path import commonprefix, relpath
        paths = [item.source for item in self.ids['stack'].children if isinstance(item, Factory.get('StackPart'))]
        common_path = commonprefix(paths)
        od['base'] = common_path
        for item in reversed(self.ids['stack'].children):
            if not isinstance(item, Factory.get('StackPart')): continue
            d=dict()
            d['qt'] = item.qt
            d['source'] = relpath(item.source, common_path)
            d['template'] = ''
            d['dual'] = not(item.verso=='normal')
            cards.append(d)
        od['cards'] = cards
        json.dump(od, file(filepath,'wb'), indent = 4)
        #Now also CSV export
        import csv
        if cards:
            my_dict = cards[0]
            with open('mycsvfile.csv', 'wb') as f:  # Just use 'w' mode in 3.x
                w = csv.DictWriter(f, my_dict.keys())
                w.writeheader()
                for card in cards:
                    w.writerow(card)

    def compute_stats(self,grid):
        if grid is None:
            grid = self.ids['stack']
        qt = 0
        qt_front = 0
        qt_back = 0
        for index,c in enumerate(grid.children):
            if not isinstance(c, Factory.get('StackPart')): continue
            c.row=len(grid.children)-index-1
            qt+=c.qt
            if c.verso == 'normal':
                qt_front+=c.qt
            else:
                qt_back+=c.qt
        num_part = len(grid.children)
        label = "Stack made of %s parts / %s Cards: %s Front - %s Back"%(num_part,qt,qt_front,qt_back)
        self.ids['stats'].text = label


class SGMApp(App):
    def build(self):
        root = BGDeckMaker()
        root.ids['file_chooser'].load_folder(gamepath)
        return root

    def compute_stats(self,grid): return self.root.compute_stats(grid)
if __name__ == '__main__':

    SGMApp().run()
