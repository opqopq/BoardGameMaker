from kivy.app import App
from kivy.factory import Factory
from kivy.uix.behaviors import ButtonBehavior, ToggleButtonBehavior
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
from fields import BaseField
from conf import gamepath, FILE_FILTER
import os, os.path

Builder.load_file('kv/sgm.kv')

class FolderTreeView(TreeView):
    folder = StringProperty()
    filters = ListProperty()
    rootpath = StringProperty()

    def on_rootpath(self, instance, value):
        self.load_folder(value)

    def load_folder(self, folder):
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

class FileViewItem(ToggleButtonBehavior, BoxLayout):
    name = StringProperty()
    source = StringProperty()
    is_all_folder = StringProperty(False)
    tmplWidget = ObjectProperty()

    def on_state(self, target, state):
        self.realise()
        if state == 'down':
            f = Factory.get('FileItemOption')()
            f.is_all_folder = self.is_all_folder
            self.add_widget(f)
            from kivy.animation import Animation
            anim = Animation(size_hint_y=0.2, duration=.1)
            anim.start(f)
        else:
        #remove the choice box
            self.remove_widget(self.children[0])

    def on_press(self):
        if self.last_touch.is_double_tap:#directly add it to the pool
            self.add_item("1", 'normal')

    def apply_item(self,name):
        from os.path import relpath
        stack = App.get_running_app().root.ids['deck'].ids['stack']
        if stack.last_selected:
            sel = stack.last_selected
            #if selected stackpart was an image, copy the source file to values, to be applied on templ
            if not sel.template:
                sel.values['default'] = sel.source
            #Replace template
            if self.name.startswith(gamepath):
                fold = relpath(self.name, gamepath)
            else:
                fold = self.name
            #Creta & open the popup for all details
            p = Factory.get('TemplateEditPopup')()
            p.name = fold
            options = p.ids['options']
            options.values = sel.values
            options.tmplPath = "@%s"%fold #trigger options building on popup
            p.stackpart = sel
            p.open()
            p.do_layout()
            p.content.do_layout()
            from kivy.clock import Clock
            def _inner(*args):
                prev = p.ids['preview']
                tmpl = prev.children[0]
                TS = tmpl.size
                PS = prev.size
                W_ratio = float(.9*PS[0])/TS[0]
                H_ratio = float(.9*PS[1])/TS[1]
                ratio = min(W_ratio, H_ratio)
                x,y = p.ids['FL'].center
                prev.center = ratio * x, ratio * y
                p.ids['preview'].scale = ratio
                #forcing x to 0
                prev.x = 5
            Clock.schedule_once(_inner, 0)

    def add_item(self, qt, verso):
            from os.path import relpath
            stack = App.get_running_app().root.ids['deck'].ids['stack']
            ##########################################################
            qt = int(qt)
            if self.is_all_folder:
                #print self, self.source, self.name, self.is_all_folder
                #It is a folder, add all the imge from folder
                for fiv in self.parent.children:
                    if fiv.is_all_folder: continue
                    if fiv.name.endswith('.csv'): continue
                    box = StackPart()
                    box.name = fiv.name
                    box.source = os.path.join(self.is_all_folder, fiv.name)
                    box.qt =qt
                    box.verso = verso
                    if fiv.name.endswith('.kv'):
                        if self.is_all_folder.startswith(gamepath):
                            fold = relpath(self.is_all_folder, gamepath)
                        else:
                            fold = self.is_all_folder
                        box.template = "@%s"%os.path.join(fold, fiv.name)
                        box.realise()
                    stack.add_widget(box)
                    from kivy.base import EventLoop
                    EventLoop.idle()
            elif self.name.endswith('.csv'):
                App.get_running_app().root.ids.deck.load_file(self.name)
            else:
                box = StackPart()
                box.name = self.name
                box.source = self.source
                box.qt = qt
                box.verso = verso
                stack.add_widget(box)
                if self.name.endswith('.kv'):
                    box.tmplWidget = self.tmplWidget
                    if self.name.startswith(gamepath):
                        fold = relpath(self.name, gamepath)
                    else:
                        fold = self.name
                    box.template = "@%s"%fold
                    box.realise()

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
            from conf import alert
            alert('Error while loading %s template'%self.name)

            return
        #App.get_running_app().root.ids['realizer'].add_widget(tmpl) #force draw of the beast
        self.tmplWidget = tmpl
        def inner(*args):
            from kivy.base import EventLoop
            EventLoop.idle()
            cim = tmpl.toImage()
            cim.texture.flip_vertical()
            self.ids['img'].texture = cim.texture
            #App.get_running_app().root.ids['realizer'].remove_widget(tmpl)
        Clock.schedule_once(inner, -1)

class SpecialViewItem(FileViewItem):
    "FileView for Folder & CSV file. Usable for script ? "
    pass

class StackPart(ButtonBehavior, BoxLayout):
    selected = BooleanProperty(False)
    row = NumericProperty(0)
    template = StringProperty()
    tmplWidget = ObjectProperty()
    name = StringProperty()
    values = DictProperty()
    source = StringProperty()

    def realise(self,withValue = False):
        #Force the creation of an image from self.template, thourhg real display
        from kivy.clock import Clock
        #Force the creaiotn of the tmpl miniture for display
        from template import BGTemplate
        if not self.template:
            return
        try:
            tmpl = BGTemplate.FromFile(self.template)[-1]
        except IndexError:
            print 'Warning: template file %s contains no Template !!'%self.template
            from conf import alert
            alert('Error while loading template %s '%self.template)
            return
        #App.get_running_app().root.ids['realizer'].add_widget(tmpl) #force draw of the beast

        if withValue:
            tmpl.apply_values(self.values)
        def inner(*args):
            #Here is hould loop on the template to apply them on values
            from kivy.base import EventLoop
            EventLoop.idle()
            self.tmplWidget = tmpl
            cim = tmpl.toImage()
            cim.texture.flip_vertical()
            self.ids['img'].texture = cim.texture
            #App.get_running_app().root.ids['realizer'].remove_widget(tmpl)
        Clock.schedule_once(inner, -1)

    def on_press(self):
        self.selected = not(self.selected)
        if self.selected: #update on dad selection
            if self.parent.last_selected and self.parent.last_selected != self:
                self.parent.last_selected.selected = False
            self.parent.last_selected = self

    def on_selected(self, instance, selected):
        if self.template:
            self.realise(True)
        if self.selected:
            from kivy.uix.boxlayout import BoxLayout
            BOX = BoxLayout(orientation='vertical', size_hint=(None, None))
            #Add Remove Button
            b = Factory.get('HiddenRemoveButton')(icon='trash')
            b.bind(on_press=lambda x: self.parent.remove_widget(self))
            #self.add_widget(b)
            from kivy.animation import Animation
            W = 100
            if self.template:#it is a template: add edit button
                W = 90
                be = Factory.get('HiddenRemoveButton')(icon='edit')
                def inner(*args):
                    p = Factory.get('TemplateEditPopup')()
                    p.name = self.template
                    options = p.ids['options']
                    #print 'editing options with ', self.values
                    options.values = self.values
                    options.tmplPath = self.template #trigger options building on popup
                    p.stackpart = self
                    p.open()
                    p.do_layout()
                    p.content.do_layout()
                    from kivy.clock import Clock
                    def _inner(*args):
                        prev = p.ids['preview']
                        tmpl = prev.children[0]
                        TS = tmpl.size
                        PS = prev.size
                        W_ratio = float(.9*PS[0])/TS[0]
                        H_ratio = float(.9*PS[1])/TS[1]
                        ratio = min(W_ratio, H_ratio)
                        x, y = p.ids['FL'].center
                        prev.center = ratio * x, ratio * y
                        p.ids['preview'].scale = ratio
                        #forcing x to 0
                        prev.x = 5

                    Clock.schedule_once(_inner, 0)
                be.bind(on_press = inner)
                #self.add_widget(be)
                BOX.add_widget(be)
                anim = Animation(width=W, duration=.1)
                anim.start(be)
            BOX.add_widget(b)
            self.add_widget(BOX)
            anim = Animation(width=W, duration=.1)
            anim.start(b)
        else:
            self.remove_widget(self.children[0])
            #if self.template:
            #    self.remove_widget(self.children[0])

    def Copy(self):
        blank = self.__class__()
        for attr in ['template','name','values', "qt","verso"]:
            setattr(blank, attr, getattr(self,attr))
        blank.ids['img'].texture = self.ids['img'].texture
        return blank

class TemplateEditTree(TreeView):
    "Use in Template Edit Popup to display all possible fields"
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
            tmpl.apply_values(self.values)
            #Now add on load
            node = self.add_node(TreeViewLabel(text=tmpl.template_name, color_selected=(.6,.6,.6,.8)))
            node.is_leaf = False #add the thingy
            #point to the template
            node.template = tmpl
            #Deal with Template Properties:
            for pname, editor in tmpl.vars.items():
                self.add_node(TreeViewField(name=pname, editor=editor(tmpl)), node)
            #Deal with KV style elemebts
            for fname in tmpl.ids.keys():
                if not isinstance(tmpl.ids[fname], BaseField):
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
        values = tree.values
        print 'ols vlu', values
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
                        print child, key, sv

        print 'values is ', values
        self.stackpart.values = values
        self.stackpart.tmplWidget = tmpl
        oldname = self.stackpart.template
        if '@' in oldname:
            oname,opath = oldname.split('@')
        else:
            oname,opath = oldname,""
        if opath:
            self.stackpart.template = '%s@%s'%(tmpl.template_name, opath)
        else:
            self.stackpart.template = tmpl.template_name
        cim =  tmpl.toImage()
        cim.texture.flip_vertical()
        self.stackpart.ids['img'].texture = cim.texture

class BGDeckMaker(BoxLayout):
    cancel_action = BooleanProperty(False)

    tmplsLib = ObjectProperty()

    def empty_stack(self):
        self.ids['stack'].clear_widgets()

    def prepare_print(self):
        from printer import prepare_pdf
        from conf import card_format
        FFORMAT = (card_format.width, card_format.height)
        #Do that only if fit format is not forced
        if not self.ids['force_format'].active:
            sizes = set()
            for cs in self.ids['stack'].children:
                if not isinstance(cs, StackPart):
                    continue
                if not cs.template:
                    sizes.add(FFORMAT)
                else:
                    if cs.tmplWidget:
                        sizes.add(tuple(cs.tmplWidget.size))
                    else:
                        from template import BGTemplate
                        sizes.add(BGTemplate.FromFile(cs.template).size)
            if len(sizes) == 1:
                FFORMAT = sizes.pop()
        #Now add the advancement gauge
        progress = self.ids['load_progress']
        progress.value = 0
        size, book = prepare_pdf(self.ids['stack'], FFORMAT)
        progress.max = size
        from kivy.clock import Clock
        step_counter = range(size)

        def inner(*args):
            step_counter.pop()
            progress.value +=1
            book.generation_step()
            if not step_counter:
                Clock.unschedule(inner)
                book.save()
                book.show()
                from conf import alert
                alert('PDF Export completed')

        Clock.schedule_interval(inner,.1)
        return True

        Clock.schedule_interval(inner,.1)

    def load_template_lib(self, force_reload = False, background_mode = False):
        #Same as load_folder('/Templates') but with delay to avoid clash
        progress = self.ids['load_progress']
        pictures = self.ids['pictures']
        if background_mode:
            pictures = Factory.get('PictureGrid')()
        pictures.clear_widgets()
        if self.tmplsLib and not force_reload:
            for c in reversed(self.tmplsLib):
                if c.parent:
                    c.parent.remove_widget(c)
                pictures.add_widget(c)
            return
        from template import templateList
        tmpls = sorted([x for x in os.listdir('Templates') if x.endswith('.kv')], key=lambda x:x.lower() , reverse=True)
        C = len(tmpls)
        progress.max = C
        progress.value = 1

        def inner(*args):
            if not tmpls:
                Clock.unschedule(inner)
                self.tmplsLib = pictures.children[:]
                return
            _f = os.path.join('Templates',tmpls.pop())
            templateList.register_file(_f)
            img = FileViewItem(source="", name=_f)
            pictures.add_widget(img)
            progress.value += 1
            img.realise()
        Clock.schedule_interval(inner, .1)

    def load_folder(self, folder):
        self.cancel_action = False
        if not folder:
            return
        progress = self.ids['load_progress']
        pictures = self.ids['pictures']
        pictures.clear_widgets()
        C = len([x for x in os.listdir(folder) if x.endswith(FILE_FILTER)])
        progress.max = C
        progress.value = 1
        #pg = Factory.get('PictureGrid')()
        pictures.add_widget(SpecialViewItem(source='folder-add', is_all_folder=folder, name="Add %d Imgs"%C))
        docs = sorted([x.lower() for x in os.listdir(folder) if x.endswith(FILE_FILTER)], reverse=True)
        #ensure the stop button is reachable
        self.ids['stop_action'].width = 80
        self.ids['stop_action'].text = 'Stop'
        def inner(*args):
            if docs:
                _f = docs.pop()
                if _f.endswith('.kv'): #it is a template:
                    source = 'img/card_template.png'
                    _f = os.path.join(folder, _f)
                elif _f.endswith('.csv'):
                    source = 'csv'
                    _f = os.path.join(folder, _f)
                else:
                    source  = os.path.join(folder,_f)
                if _f.endswith('.csv'):
                    img = SpecialViewItem(source= source, name=_f)
                else:
                    img = FileViewItem(source=source, name=_f)
                pictures.add_widget(img)
                progress.value += 1
                if _f.endswith('.kv'):
                    img.realise()
            if self.cancel_action or not docs:
                self.cancel_action = True
                Clock.unschedule(inner)
                self.ids['stop_action'].width = 0
                self.ids['stop_action'].text = ''
                progress.value = 0
                return False
        Clock.schedule_interval(inner,.025)

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

    def choose_file_popup(self,title, cb):
        from kivy.uix.popup import Popup
        from kivy.uix.filechooser import FileChooserListView
        from conf import get_last_dir, set_last_dir
        f = FileChooserListView(path =get_last_dir(self))
        def valid(*args):
            p.dismiss()
        f.bind(on_submit= valid)
        p = Popup(content=f)
        p.title = title
        def inner(*args):
            if p.content.selection:
                selection = p.content.selection[0]
                from os.path import split
                set_last_dir(self,split(selection)[0])
                cb(selection)
        p.on_dismiss = inner
        p.open()

    def write_file_popup(self,title,cb):
        p = Factory.get('WriteFilePopup')()
        p.title = title
        p.cb = cb
        p.open()

    def load_file(self, filepath='mycsvfile.csv'):
        #Now also CSV export
        import csv
        with open(filepath, 'rb') as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=";,")
            csvfile.seek(0)
            reader = csv.DictReader(csvfile, dialect=dialect)
            header = reader.fieldnames
            stack = self.ids['stack']
            remaining_header = set(header) - set(['qt', 'source', 'template', 'dual'])
            boxes = list()
            for index, obj in enumerate(reader):
                #print index, obj
                if set([obj[_v] for _v in obj]) == set(dialect.delimiter):#skipping empty row made of ;;;;;; or ,,,,,
                    continue
                qt = 1
                if 'qt' in obj:
                    qt = int(obj['qt'])
                verso = 'normal'
                if 'dual' in obj:
                    if not obj['dual'] or obj['dual'].lower() == 'false':
                        verso = 'normal'
                    else:
                        verso = 'down'
                box = StackPart()
                box.verso = verso
                box.qt = qt
                if 'template' in obj and obj['template']:
                    box.template = obj['template']
                if 'source' in obj and obj['source']:
                    box.source = obj['source']
                values = dict()
                for attr in remaining_header:
                    v = obj.get(attr, '')
                    if v is not '':#'' means cell is empty
                        if isinstance(v, basestring):
                            v= unicode(v, 'latin-1')
                        values[attr] = v
                box.values = values
                stack.add_widget(box)
                boxes.append(box)
            boxes.reverse()
            def inner(*args):
                b= boxes.pop()
                b.realise(withValue=True)
                if not boxes:
                    Clock.unschedule(inner)
                    print 'Import/Inner is over'
            Clock.schedule_interval(inner, .1)

    def export_file(self, filepath='mycsvfile.csv'):
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
                if item.template and item.source == 'img/card_template.png':
                    _s = ""
                d['source'] = _s
            else:
                d['source'] = ""
            if item.template:
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
                fields_order = ['qt','dual','source','template'] + my_dict.keys()[:]
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
            if not isinstance(c, Factory.get('StackPart')):
                continue
            c.row = len(grid.children)-index
            qt += c.qt
            if c.verso == 'normal':
                qt_front += c.qt
            else:
                qt_back += c.qt
        num_part = len([_c for _c in grid.children if isinstance(_c, StackPart)])
        label = "Stack made of %s parts / %s Cards: %s Front - %s Back"%(num_part,qt,qt_front,qt_back)
        self.ids['stats'].text = label

class SGMApp(App):
    def compute_stats(self,grid): return self.root.compute_stats(grid)
if __name__ == '__main__':
    SGMApp().run()
