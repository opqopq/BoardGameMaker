"Define the Template class and some template examples"
__author__ = 'MRS.OPOYEN'


from fields import Field
from kivy.properties import NumericProperty, OptionProperty, ObjectProperty, DictProperty, StringProperty
from fields import ImageField
from kivy.factory import Factory
from collections import OrderedDict
from editors import editors_map
from kivy.uix.relativelayout import RelativeLayout
from os.path import isdir
from conf import path_reader

class BGTemplate(Field, RelativeLayout):
    """Template class. Made of fields able to render an image"""
    Type = "Template"
    # dpi = NumericProperty(150, name="DPI")
    name = "TMPL"
    source = OptionProperty('text', options=['file', 'text'])
    not_exported = ['ids', 'src']

    def __repr__(self):
        return '<Template #%s>'%self.name

    @classmethod
    def FromFile(cls, filename):
        from os.path import abspath, isfile, join
        from conf import gamepath
        if "@" in filename: #Only using subone
            name, filename = filename.split('@')
        else:
            name = ""
        if not isfile(filename):
            #try with gamepath ?
            if isfile(join(gamepath,path_reader(filename))):
                filename = join(gamepath, path_reader(filename))
        #Here, we convert to abspath / normpath, as filename is used to index rules by kivy. avoid reimporting rules
        filepath = abspath(path_reader(filename))
        filename = filepath
        #Load  & return all templates from a file as a list. Take an optionnal filter
        from kivy.lang import Builder
        # Remove any former trace of the file
        Builder.unload_file(filename)
        # Now create a widget
        try:
            Builder.load_file(filename)
            res = cls._process_file_build(filename)
        except Exception, E:
            from conf import log, alert
            import traceback
            alert(str(E))
            print 'Error while trying to import Template ',filename
            log(E, traceback.print_exc())
            res = list()
        if name:
            return [r for r in res if r.name == name ]
        return res

    @classmethod
    def _process_last_build(cls):
        from kivy.lang import Builder
        #Get last rules imported for template creation
        k,r = Builder.rules[-1]
        p = r.ctx
        if not p.dynamic_classes:
            #Old school technique: get last rules
            from kivy.logger import Logger
            Logger.warn('Registering through old technique with .Klass:', k.key)
            t = BGTemplate()
            t.cls = (k.key,)
            Builder.apply(t)
            t.name = k.key
        else:
            kkey = p.dynamic_classes.keys()[0]
            t = Factory.get(kkey)()
            t.name = kkey
            #Now forcing id values to name
            for ID in t.ids:
                t.ids[ID].name = ID
        return t

    @classmethod
    def _process_file_build(cls,filename):
        from kivy.lang import Builder
        res = list()
        #factory unload
        # Get all rules from files
        rules = [x for x in Builder.rules if x[1].ctx.filename == filename]
        attrs= dict()
        ctxs = set()
        for k,r in rules:
            ctxs.add(r.ctx)
            attrs[k] = (k.match, r.properties.keys())
        for ctx in ctxs:
            for dclass in ctx.dynamic_classes:
                t = Factory.get(dclass)()
                if isinstance(t, BGTemplate):
                    t.name = dclass
                    for ID in t.ids:
                        #Force field name to ID
                        t.ids[ID].name = ID
                    t.src = filename
                    if not t.attrs:
                        #force a reset of orederedict to avoid singleton effect
                        t.attrs = OrderedDict()
                        #fill attrs with default ones
                        for (m,ats) in attrs.values():
                            if m(t):
                                props = t.properties()
                                for pname in ats:
                                    pklass = props[pname]
                                    if pklass.__class__ == ObjectProperty:
                                        if getattr(t,pname).__class__ in editors_map:
                                            t.attrs[pname] = editors_map[getattr(t,pname).__class__]
                                    else:
                                        if pklass.__class__ in editors_map:
                                            t.attrs[pname] = editors_map[pklass.__class__]
                    res.append(t)
        return res

    @classmethod
    def FromText(cls, text):
        from kivy.lang import Builder
        #Now create a widget
        Builder.load_string(text)
        res = cls._process_last_build()
        return res

    @classmethod
    def FromField(cls, field):
        "Create a whole template base on a single field"
        class FromFieldTemplate(BGTemplate):
            def __init__(self, **kwargs):
                BGTemplate.__init__(self, **kwargs)
                self.name = "%s Wrapper"%field.Type
                self.add_widget(field.Copy())
                field.size = self.size
                self.attrs = field.attrs.copy()
        return FromFieldTemplate()

    def export_to_image(self, filename=None, bg_col = (1,1,1,0)):
        from kivy.graphics import Canvas, Translate, Fbo, ClearColor, ClearBuffers, Scale


        if filename is None:
            #resorting to default build on id
            filenmame = 'build/%s.png'%id(self)
        if self.parent is not None:
            canvas_parent_index = self.parent.canvas.indexof(self.canvas)
            self.parent.canvas.remove(self.canvas)

        fbo = Fbo(size=self.size, with_stencilbuffer=True)

        with fbo:
            ClearColor(*bg_col)
            ClearBuffers()
            Scale(1, -1, 1)
            Translate(-self.x, -self.y - self.height, 0)

        fbo.add(self.canvas)
        fbo.draw()
        fbo.texture.save(filename, flipped=False)
        fbo.remove(self.canvas)

        if self.parent is not None:
            self.parent.canvas.insert(canvas_parent_index, self.canvas)

        return True

    def toImage(self, bg_color=(1,1,1,0)):
        #create image widget with texture == to a snapshot of me
        from kivy.graphics import Canvas, Translate, Fbo, ClearColor, ClearBuffers, Scale
        from kivy.core.image import Image as CoreImage

        if self.parent is not None:
            canvas_parent_index = self.parent.canvas.indexof(self.canvas)
            self.parent.canvas.remove(self.canvas)

        fbo = Fbo(size=self.size, with_stencilbuffer=True)

        with fbo:
            ClearColor(*bg_color)
            ClearBuffers()
            Scale(1, -1, 1)
            Translate(-self.x, -self.y - self.height, 0)

        fbo.add(self.canvas)
        fbo.draw()

        cim = CoreImage(fbo.texture, filename = '%s.png'%id(self))

        fbo.remove(self.canvas)

        if self.parent is not None:
            self.parent.canvas.insert(canvas_parent_index, self.canvas)

        return cim

    def blank(self):
        t = self.__class__()
        t.cls = self.cls
        t.name = self.name
        t.Type = self.Type
        return t

    def apply_values(self, values):
        #print 'appy_values', self, values
        childrens = self.ids.values()
        for k,v in values.items():
            if '.' not in k:
                for cname in self.ids.keys():
                    if cname == k and getattr(self.ids[cname],'default_attr'):
                        print 'resorting to default attr', self.ids[cname], k, getattr(self.ids[cname],'default_attr'), v
                        setattr(self.ids[cname], getattr(self.ids[cname],'default_attr'), v)
                        break
                else:
                    setattr(self,k,v)
            else:
                childName, attrName = k.split('.', 2)
                for cname in self.ids.keys():
                    if cname == childName:
                        if isinstance(self.ids[cname], ImageField):
                            self.ids[cname].source = v
                        setattr(self.ids[cname], attrName, v)
                for child in self.children:
                    if child in childrens:
                        continue
                    if child.id == childName:
                        if isinstance(child, ImageField):
                            child.source = v
                        setattr(child, attrName, v)

#Now define the cache foundry for all templates
from kivy._event import EventDispatcher
from kivy.properties import DictProperty

class TemplateList(EventDispatcher):
    templates = DictProperty()

    def copy(self):
        return self.templates.copy()


    def __setitem__(self, key, value):
        #print 'registering template',key
        self.templates[key] = value

    def __getitem__(self,name):
        #If the desired result is a file namee, reload it from file
        res = self.templates[name]
        if isinstance(res, basestring):
            #print 'reloading', res
            return BGTemplate.FromFile(res)[-1]
        return res

    def register(self,tmpl):
        self[tmpl.name] = tmpl

    def register_file(self, filename):
        for tmpl in BGTemplate.FromFile(filename):
            self[tmpl.name] = tmpl
            tmpl.src = filename
            tmpl.source = 'file'

    def refresh(self, tmplName):
        tmpl = self[tmplName]
        if tmpl.source =='file':
            self.register_file(tmpl.src)
templateList = TemplateList()

#Now for some easy example
class EmptyKlass(BGTemplate):
    def __init__(self,*args,**kwargs):
        BGTemplate.__init__(self)
        self.name = "EmptyKlass"
        from fields import ImageField
        img = ImageField()
        #img.x = img.y = 0
        img.id = "default"
        #img.width = self.width
        #img.height = self.height
        img.keep_ratio = True
        img.scale = True
        self.add_widget(img)
        from kivy.metrics import cm
        self.size = (cm(6.35), cm(8.8))
        #img.size = self.size
        #img.size_hint=1,1

#templateList['EmptyKlass'] = EmptyKlass()

default_tmpl = """
#:import CARD conf.card_format
<Default@BGTemplate>:
    size: CARD.width, CARD.height
    ImageField:
        id: default
        keep_ratio: True
        allow_stretch: True
        size: root.size
"""
templateList['Default'] = BGTemplate.FromText(default_tmpl)

class RedSkin(BGTemplate):
    def __init__(self, *args, **kwargs):
        BGTemplate.__init__(self, *args, **kwargs)
        self.name = "RedSkinKlass"
        from fields import ColorField
        color = ColorField()
        #color.id = "deffault"
        color.width = self.width
        color.height = self.height
        color.opacity= .5
        color.rgba = (1,0,0,1)
        self.add_widget(color)
        from kivy.metrics import cm
        self.size = color.size = (cm(6.5),cm(8.8))
        from kivy.clock import Clock

#templateList.register(RedSkin())


#Now load all files from the Templates dir to templatelist
def LoadTemplateFolder(folder="Templates"):
    from glob import glob
    from os.path import join
    for kv in glob(join(folder, '*.kv')):
        templateList.register_file(kv)
        #for tmpl in BGTemplate.FromFile(kv):
        #    templateList.register(tmpl)


from conf import CP
if CP.getboolean('Startup', 'LOAD_TMPL_LIB'):
    LoadTemplateFolder()
else:
    print 'No Template Libray Loading requested'