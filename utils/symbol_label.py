from kivy.core.text.markup import MarkupLabel
from kivy.core.text.text_pygame import LabelPygame
from kivy.core.text import Label as CoreLabel
from kivy.graphics.texture import Texture
from kivy.uix.label import Label
from kivy.utils import platform
from kivy.parser import parse_color
from kivy.logger import Logger
import re
from copy import copy
import pygame
from kivy.properties import DictProperty
from math import ceil

class SymbolCoreLabel(MarkupLabel):
        
    def _render_image(self,src,x,y,image_part=None):
        #print 'Rendering Image at src %s at %s:%s'%(src,x,y)
        #Load from PIL, then feed it to pygame. Why ????! 
        import Image
        image=Image.open(src)
        image.getdata()
        channels= list(image.split())
        #switching r and b in rgb
        channels[0],channels[2]=channels[2],channels[0]
        image= Image.merge(image.mode,channels)
        mode = image.mode
        size = image.size
        data = image.tostring()

        image_surface = pygame.image.fromstring(data, size, mode)
        # image_surface = pygame.image.load(src)

        image_surface = image_surface.convert_alpha()

        W,H=self.get_extents("_")
        image_surface= pygame.transform.scale(image_surface,(W,H))

        #image_part = (10,10,30,30) # left,top,width,height of image area
        self._pygame_surface.blit(image_surface,(x,y),None, pygame.BLEND_RGBA_ADD)

    def __init__(self, *largs, **kwargs):
        self._style_stack = {}
        self._refs = {}
        super(SymbolCoreLabel, self).__init__(*largs, **kwargs)
        # self.options['symbol']=kwargs.get('symbol',False)
        # self.options['symbol_src']=kwargs.get('symbol_src',"red.png")
        # self.options['symbol_dict']=kwargs.get('symbol_dict',dict())
        self.guiLabel=kwargs['guiLabel']
        self.options['symbol']=False


    @property
    def markup(self):
        '''Return the text with all the markup splitted::

            >>> MarkupLabel('[b]Hello world[/b]').markup
            >>> ('[b]', 'Hello world', '[/b]')

        '''
        s = re.split('(\%s|\%s)'%(self.guiLabel.start_symbol,self.guiLabel.end_symbol),self.label)
        s = [x for x in s if x != '']
        return s

    def _real_render(self):
        # use the lines to do the rendering !
        self._render_begin()

        r = self._render_text
        i = self._render_image
        # convert halign/valign to int, faster comparaison
        av = {'top': 0, 'middle': 1, 'bottom': 2}[self.options['valign']]
        ah = {'left': 0, 'center': 1, 'right': 2}[self.options['halign']]

        y = 0
        w, h = self._size
        refs = self._refs
        txt_height = sum(line[1] for line in self._lines)

        for line in self._lines:
            lh = line[1]
            lw = line[0]

            # horizontal alignement
            if ah == 0:
                x = 0
            elif ah == 1:
                x = int((w - lw) / 2)
            else:
                x = w - lw

            # vertical alignement
            if y == 0:
                if av == 1:
                    y = int((h - txt_height) / 2)
                elif av == 2:
                    y = h - (txt_height)

            for pw, ph, part, options in line[2]:
                self.options = options
                if not options.get('symbol',False):
                    r(part, x, y + (lh - ph) / 1.25)
                else:
                    try:
                        i(options.get('symbol_src'), x ,y + (lh - ph) / 1.25)
                    except pygame.error,_exc:
                        Logger.warning('Not able to load symbol: %s'%_exc)
                        r(part, x, y + (lh - ph) / 1.25)
                # should we record refs ?
                ref = options['_ref']
                if ref is not None:
                    if not ref in refs:
                        refs[ref] = []
                    refs[ref].append((x, y, x + pw, y + ph))

                #print 'render', repr(part), x, y, (lh, ph), options
                x += pw
            y += line[1]

        # get data from provider
        data = self._render_end()
        assert(data)

        # create texture is necessary
        texture = self.texture
        mipmap = self.options['mipmap']
        if texture is None or \
                self.width != texture.width or \
                self.height != texture.height:
            texture = Texture.create_from_data(data, mipmap=mipmap)
            data = None
            texture.flip_vertical()
            texture.add_reload_observer(self._texture_refresh)
            self.texture = texture

        # update texture
        # If the text is 1px width, usually, the data is black.
        # Don't blit that kind of data, otherwise, you have a little black bar.
        if data is not None and data.width > 1:
            texture.blit_data(data)

    def _pre_render(self):
        # split markup, words, and lines
        # result: list of word with position and width/height
        # during the first pass, we don't care about h/valign
        self._lines = lines = []
        self._refs = {}
        self._anchors = {}
        spush = self._push_style
        spop = self._pop_style
        options = self.options
        options['_ref'] = None
        for item in self.markup:
            # print "Rendering Item %s during _pre_render"%item
            if item == '[b]':
                spush('bold')
                options['bold'] = True
                self.resolve_font_name()
            elif item == '[/b]':
                spop('bold')
                self.resolve_font_name()
            elif item  == self.guiLabel.start_symbol:
                spush('symbol')
                options['symbol']=True
            elif item == self.guiLabel.end_symbol:
                spop('symbol')
                options['symbol']=False
            elif item == '[i]':
                spush('italic')
                options['italic'] = True
                self.resolve_font_name()
            elif item == '[/i]':
                spop('italic')
                self.resolve_font_name()
            elif item[:6] == '[size=':
                try:
                    size = int(item[6:-1])
                except ValueError:
                    size = options['font_size']
                spush('font_size')
                options['font_size'] = size
            elif item == '[/size]':
                spop('font_size')
            elif item[:7] == '[color=':
                color = parse_color(item[7:-1])
                spush('color')
                options['color'] = color
            elif item == '[/color]':
                spop('color')
            elif item[:6] == '[font=':
                fontname = item[6:-1]
                spush('font_name')
                options['font_name'] = fontname
                self.resolve_font_name()
            elif item == '[/font]':
                spop('font_name')
                self.resolve_font_name()
            elif item[:5] == '[ref=':
                ref = item[5:-1]
                spush('_ref')
                options['_ref'] = ref
            elif item == '[/ref]':
                spop('_ref')
            elif item[:8] == '[anchor=':
                ref = item[8:-1]
                if len(lines):
                    x, y = lines[-1][0:2]
                else:
                    x = y = 0
                self._anchors[ref] = x, y
            elif options['symbol']:
                # Check if symbol proposed belongs to current symbol dict. If not, go out of symbol mode
                if item in self.guiLabel.symbol_dict:
                    options['symbol_src']=self.guiLabel.symbol_dict.get(item,None)
                    # Create a single CHAR item, which will be replaced by the picture
                    item="_"
                else:
                    options['symbol']=False
                self._pre_render_label(item, options, lines)
            else:
                item = item.replace('&bl;', '[').replace(
                        '&br;', ']').replace('&amp;', '&')
                self._pre_render_label(item, options, lines)

        # calculate the texture size
        w, h = self.text_size
        if h < 0:
            h = None
        if w < 0:
            w = None
        if w is None:
            if not lines:
                w = 1
            else:
                w = max([line[0] for line in lines])
        if h is None:
            if not lines:
                h = 1
            else:
                h = sum([line[1] for line in lines])
        return int(ceil(w)), int(ceil(h))


class SymbolLabel(Label):
    start_symbol='[s]'
    end_symbol='[/s]'

    def __init__(self,**kwargs):
        Label.__init__(self,**kwargs)
        self.markup=True
        
    def _create_label(self):
        # create the core label class according to markup value
        if self._label is not None:
            cls = self._label.__class__
        else:
            cls = None
        if cls is not SymbolCoreLabel:
            # markup have change, we need to change our rendering method.
            d = Label._font_properties
            dkw = dict(zip(d, [getattr(self, x) for x in d]))
            # XXX font_size core provider compatibility
            if Label.font_size.get_format(self) == 'px':
                dkw['font_size'] *= 1.333
            self._label = SymbolCoreLabel(guiLabel=self,**dkw)
