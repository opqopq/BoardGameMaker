"This module define every models abstration, like a deck, a Xfo, a card....."
__author__ = 'MRS.OPOYEN'

from collections import OrderedDict
from kivy.properties import *
from kivy.uix.widget import Widget

class Stack(Widget):
    "Stack class, containings a serie of imgpack"
    def __init__(self,name, path=None):
        self.name = name
        self.path = path
        self.items = list()

    def __repr__(self):
        return "<Stack:%s>"%self.name

    def clear(self):
        self.items= OrderedDict()

    def load(self, filename):
        import csv
        with open(filename, 'rb') as csvfile:
            writer = csv.DictReader(csvfile)
            for row in writer:
                self.items.append(ImgPack.from_dict(row))

    def saveas(self, filename):
        import csv
        #First, make a set with all possible fieldsname
        fnames = set()
        for item in self.items:
            for key in item.values.keys():
                fnames.add(key)
        #Add the 3 main ones
        fnames = list(fnames)
        fnames = ['size','dual', 'template'] + fnames
        with open(filename, 'wb') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=list(fnames))
            writer.writeheader()
            for item in self.items:
                writer.writerow(item.to_dict())

    @classmethod
    def from_file(cls,filepath):
        from os.path import split
        s = Stack(name=split(filepath[-1]), path=filepath)
        s.load(filepath)
        return s


class ImgPack:
    def __init__(self, template=None, size=1, dual=False, values= None, **kwargs):
        self.size = size
        self.dual = dual
        if values is None:
            values = dict()
        self.values = values
        self.values.update(kwargs)
        self.template = template

    def __repr__(self):
        txt='Pack[%d]:%s'%(self.size, self.template)
        if self.dual:
            txt+="-Dual"
        return txt

    def copy(self):
        return ImgPack(self.template,self.size,self.dual,**self.values)

    def to_dict(self):
        res = {'size': self.size, 'dual':self.dual,'template': self.template.name}
        res.update(self.values)
        return res

    def export(self, fname=None):
        blank = self.template.blank()
        blank.apply_values(self.values)
        if fname is None:
            fname = 'build/%s.png'%id(self)
        blank.export_to_image(fname)

    @classmethod
    def from_dict(cls, other):
        from template import templateList
        res = cls(size = int(other['size']), dual = other['dual'].lower()=="true", template=templateList.templates.get(other['template']))
        values = other.copy()
        del values['dual'], values['size'], values['template']
        res.values.update(values)
        return res