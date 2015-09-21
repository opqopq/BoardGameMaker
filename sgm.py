from kivy.app import App
from kivy.factory import Factory
from kivy.uix.image import AsyncImage, Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.properties import NumericProperty, StringProperty,   DictProperty, ListProperty
from kivy.uix.treeview import  TreeViewLabel
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.treeview import TreeView
from deck import TreeViewField
from fields import Field
from conf import gamepath
import os, os.path

Builder.load_file('kv/sgm.kv')

class FolderTreeView(TreeView):
    folder = StringProperty()
    filters = ListProperty()
    rootpath = StringProperty()

    def on_rootpath(self, instance, value):
        self.load_folder(value)

    def  load_folder(self, folder):
        self.folder = folder
        from os.path import join, isdir
        from os import listdir
        self.clear_widgets()
        for f in listdir(folder):
            if not isdir(join(folder,f)) and not f.endswith(tuple(self.filters)): continue
            n = self.add_node(TreeViewLabel(text=f))
            n.is_leaf = False
            n.is_loaded = False
            n.path = join(folder, f)

    def callback(self, instance, node):
        from os import listdir
        from os.path import join, isdir
        if hasattr(node, 'path'):
            for f in listdir(node.path):
                if not isdir(join(node.path,f)):
                    continue
                n = self.add_node(TreeViewLabel(text=f), node)
                n.is_leaf = False
                n.is_loaded = False
                n.path = join(node.path, f)

    load_func = callback

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

class IconImage(ButtonBehavior, Image):
    selected = BooleanProperty(False)
    inner_box = ObjectProperty(None)
    folder = StringProperty()
    name = StringProperty()

    def on_press(self):
        if self.last_touch.is_double_tap or self.selected:
            stack = App.get_running_app().root.ids['deck'].ids['stack']
            ##########################################################
            qt = int(self.inner_box.ids['qt'].value)
            verso = self.inner_box.ids['dual'].state
            if self.folder:
                #It is a folder, add all the imge from folder
                for f in os.listdir(self.folder):
                    if f.endswith(('.jpg','.jpeg', '.png','.gif','.kv')):
                        box = StackPart()
                        box.name = f
                        box.source = os.path.join(self.folder,f)
                        box.qt =qt
                        box.verso = verso
                        if f.endswith('.kv'):
                            box.template = "@%s"%os.path.join(self.folder,f)
                            #box.source = 'img/card_template.png'
                            box.realise()
                        stack.add_widget(box)
            else:
                box = StackPart()
                box.name = self.name
                box.source = self.source
                box.qt = qt
                box.verso = verso
                stack.add_widget(box)
                if self.name.endswith('.kv'):
                    box.template="@%s"%self.name
                    #box.source = 'img/card_template.png'
                    box.realise()
            self.selected= False

        else:
            if self.parent.last_selected:
                self.parent.last_selected.selected = False
            self.selected = True
            self.parent.last_selected = self

    def on_selected(self, target,value):
        if self.selected:
            #Add QT / Dual
            self.inner_box = Factory.get('ChoiceBox')()
            self.add_widget(self.inner_box)
        else:
            #Remove QT/Dual
            self.remove_widget(self.inner_box)

    def realise(self,*args):
        if not self.name.endswith('.kv'):
            return
        #Force the creation of an image from self.template, thourhg real display
        from kivy.clock import Clock
        #Force the creaiotn of the tmpl miniture for display
        from template import BGTemplate
        try:
            tmpl = BGTemplate.FromFile(self.name)[-1]
        except IndexError:
            print 'Warning: template file %s contains no Template !!'%self.name
            return
        App.get_running_app().root.ids['realizer'].add_widget(tmpl) #force draw of the beast

        def inner(*args):
            #Here is hould loop on the template to apply them on values
            cim =  tmpl.toImage()
            cim.texture.flip_vertical()
            self.texture = cim.texture
            App.get_running_app().root.ids['realizer'].remove_widget(tmpl)
        Clock.schedule_once(inner, -1)

class StackPart(ButtonBehavior, BoxLayout):
    selected = BooleanProperty(False)
    row = NumericProperty(0)
    template = StringProperty()
    tmplWidget = ObjectProperty()
    name = StringProperty()
    values = DictProperty()

    def realise(self,*args):
        #Force the creation of an image from self.template, thourhg real display
        from kivy.clock import Clock
        #Force the creaiotn of the tmpl miniture for display
        from template import BGTemplate
        try:
            tmpl = BGTemplate.FromFile(self.template)[-1]
        except IndexError:
            print 'Warning: template file %s contains no Template !!'%self.template
            return
        App.get_running_app().root.ids['realizer'].add_widget(tmpl) #force draw of the beast

        def inner(*args):
            #Here is hould loop on the template to apply them on values
            self.tmplWidget = tmpl
            cim =  tmpl.toImage()
            cim.texture.flip_vertical()
            self.ids['img'].texture = cim.texture
            App.get_running_app().root.ids['realizer'].remove_widget(tmpl)
        Clock.schedule_once(inner, -1)

    def on_press(self):
        if self.last_touch.is_double_tap :
            self.selected= False
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
            if self.template:#it is a template: add edit button
                be = Factory.get('HiddenRemoveButton')(source='img/writing_blue.png')
                def inner(*args):
                    p = Factory.get('TemplateEditPopup')()
                    p.name = self.template
                    options = p.ids['options']
                    print 'editing options with ', self.values
                    options.values = self.values
                    options.tmplPath = self.template #trigger options building on popup
                    p.stackpart = self
                    p.open()
                be.bind(on_press = inner)
                self.add_widget(be)
                anim = Animation(width=100, duration=.1)
                anim.start(be)
        else:
            self.remove_widget(self.children[0])
            if self.template:
                self.remove_widget(self.children[0])

    def Copy(self):
        blank = self.__class__()
        for attr in ['template','name','values', "qt","verso"]:
            setattr(blank, attr, getattr(self,attr))
        blank.ids['img'].texture = self.ids['img'].texture
        return blank

class TemplateEditTree(TreeView):
    tmplPath = StringProperty()
    current_selection = ObjectProperty()
    values = DictProperty() #values from template, if any

    def update_tmpl(self,tmpl):
        self.target.clear_widgets()
        self.target.add_widget(tmpl)
        self.current_selection = (tmpl, self.selected_node)

    def on_tmplPath(self, instance, value):
        from template import BGTemplate
        #tmplPath is in the form [NAME][@PATH]. If path provided, load all tmpl from there. Without it, take name from library
        name, path = self.tmplPath.split('@')
        if not(name) and not(path):
            print 'Warning: tmpl Path is empty. stopping template edition'
        if not path:
            from template import templateList
            tmpls = [templateList[name]]
        else:
            tmpls = BGTemplate.FromFile(path)
        for tmpl in tmpls:
            #Ensure we have the proper values validated
            tmpl.apply_values(self.values)
            #Now add on load
            node = self.add_node(TreeViewLabel(text=tmpl.name, color_selected=(.6,.6,.6,.8)))
            node.is_leaf = False #add the thingy
            #point to the template
            node.template = tmpl
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
            self.toggle_node(node)
            self.select_node(node) # will issue a template update

class TemplateEditPopup(Popup):
    def compute(self):
        tree = self.ids['options']
        if not tree.current_selection:
            print 'Warning: no template choosen. do nothing'
            return
        tmpl, node = tree.current_selection
        #Here is hould loop on the template to apply them on values
        values = dict()
        if node:#do that only if a template has been selected. otherwise skip it
            for child_node in node.nodes:
                for child in child_node.walk(restrict=True):
                    key = getattr(child, 'target_key',None)
                    sv = getattr(child, 'stored_value',None)
                    if key is not None and sv is not None: # means somthing has changed
                        if child.target_attr in tmpl.vars: #just a tmpl variable
                            values[key] = sv
                        else:
                             values["%s.%s"%(child.target_attr, key)] = sv
        self.stackpart.values = values
        self.stackpart.tmplWidget = tmpl
        oldname = self.stackpart.template
        if '@' in oldname:
            oname,opath = oldname.split('@')
        else:
            oname,opath = oldname,""
        if opath:
            self.stackpart.template = '%s@%s'%(tmpl.name, opath)
        else:
            self.stackpart.template = tmpl.name
        cim =  tmpl.toImage()
        cim.texture.flip_vertical()
        self.stackpart.ids['img'].texture = cim.texture

class BGDeckMaker(BoxLayout):
    cancel_load = BooleanProperty()

    def empty_stack(self):
        self.ids['stack'].clear_widgets()

    def prepare_print(self):
        from printer import prepare_pdf
        from conf import card_format
        prepare_pdf(self.ids['stack'], (card_format.width, card_format.height))

    def load_template_lib(self):
        #Same as load_folder('/Templates') but with delay to avoid clash
        for kv in os.listdir('Templates'):
            if not kv.endswith('.kv'): continue
        progress = self.ids['load_progress']
        pictures = self.ids['pictures']
        pictures.clear_widgets()
        tmpls = sorted([x for x in os.listdir('Templates') if x.endswith('.kv')])
        C = len(tmpls )
        progress.max = C
        progress.value = 1
        pg = Factory.get('PictureGrid')()
        def inner(*args):
            if not tmpls:
                Clock.unschedule(inner)
                return
            _f = os.path.join('Templates',tmpls.pop())
            img = IconImage(source="", name=_f)
            pictures.add_widget(img)
            progress.value += 1
            img.realise()
        Clock.schedule_interval(inner, .1)

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
                #source = 'img/card_template.png'
                source = ""
                _f = os.path.join(folder, _f)
            else:
                source  = os.path.join(folder,_f)
            img = IconImage(source=source, name=_f)
            _pictures.add_widget(img)
            _progress.value += 1
            if _f.endswith('.kv'):
                img.realise()
        for index,f in enumerate(sorted(os.listdir(folder))):
            if f.endswith(('.jpg','.jpeg', '.png','.gif', '.kv')):
                Clock.schedule_once(partial(inner, f, pg, progress),0.001*index)
        def complete(*args):
            #have the grid appear in here
            pg_scroll = self.ids['pg_scroll']
            self.ids['pg_scroll'].remove_widget(pictures)
            pg_scroll._viewport = None
            pg_scroll.add_widget(pg)
            self.ids['pictures'] = pg
        Clock.schedule_once(complete, 0.01*(index+1))
        #self.ids['options'].folded = FOLD

    def load_file_json(self, filepath='deck.json'):
        import json
        od = json.load(file(filepath,'rb'))
        cards = od['cards']
        stack = self.ids['stack']
        for obj in cards:
            qt = int(obj['qt'])
            verso = 'down' if obj['dual'] else 'normal'
            box = StackPart()
            box.source = obj['source']
            box.qt = qt
            box.verso = verso
            box.template = obj['template']
            box.values = obj['values']
            stack.add_widget(box)

    def load_file(self, filepath='mycsvfile.csv'):
        #Now also CSV export
        import csv
        reader = csv.DictReader(file(filepath, 'rb'))
        header = reader.fieldnames
        stack = self.ids['stack']
        print 'reading file with header', header
        remaining_header = set(header) - set(['qt','source','template','dual'])
        for index, obj in enumerate(reader):
            qt = int(obj['qt'])
            verso = 'down' if obj['dual'] else 'normal'
            box = StackPart()
            box.source = obj['source']
            box.qt = qt
            box.verso = verso
            box.template = obj['template']
            values = dict()
            for attr in remaining_header:
                v = obj.get(attr, None)
                if v is not None:
                    values[attr] = v
            box.values = values
            stack.add_widget(box)

    def export_file(self, filepath='mycsvfile.csv'):
        print 'do the relapth for template and values also'
        from collections import OrderedDict
        from conf import gamepath
        from os.path import relpath, isfile
        import json
        od = OrderedDict()
        cards = list()
        for item in reversed(self.ids['stack'].children):
            if not isinstance(item, Factory.get('StackPart')): continue
            d=dict()
            d['qt'] = item.qt
            if item.source:
                if isfile(item.source): #it is a full path. convert it
                    _s = relpath(item.source, gamepath)
                else:
                    _s = item.source
                d['source'] = _s
            else:
                d['source'] = ""
            d['template'] = item.template
            d['dual'] = not(item.verso=='normal')
            d['values'] = item.values
            cards.append(d)
        od['cards'] = cards
        print 'skipping export to json'
        #json.dump(od, file(filepath,'wb'), indent = 4)
        #Now also CSV export
        import csv
        if cards:
            my_dict = {}
            #update the dict with all possible 'values' keys
            for c in cards:
                if c['values']:
                    my_dict.update(**c['values'])

            with open(filepath, 'wb') as f:  # Just use 'w' mode in 3.x
                fields_order = ['qt','dual','template','source'] + my_dict.keys()[:]
                w = csv.DictWriter(f, fields_order)
                w.writeheader()
                for c in cards:
                    for k in my_dict: my_dict[k]=None
                    my_dict.update(c)
                    del my_dict['values']
                    my_dict.update(**c['values'])
                    w.writerow(my_dict)

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
    def compute_stats(self,grid): return self.root.compute_stats(grid)
if __name__ == '__main__':
    SGMApp().run()
