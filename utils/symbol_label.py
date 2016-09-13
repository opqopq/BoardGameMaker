from kivy.core.text.markup import MarkupLabel
from kivy.core.text import Label as CoreLabel
from kivy.graphics.texture import Texture
from kivy.uix.label import Label, get_hex_from_color
from kivy.utils import platform
from kivy.parser import parse_color
from kivy.logger import Logger
import re
from copy import copy
from kivy.properties import StringProperty
from kivy.core.text.text_layout import layout_text, LayoutWord
from kivy.properties import DictProperty


class SymbolCoreLabel(MarkupLabel):
        
    def _render_image(self,src, x, y, image_part=None):
        from utils import find_path
        from PIL import Image
        from img_xfos import img_modes
        #print 'Rendering Image at src %s at %s:%s'%(src,x,y), 'for a size of ',
        src = find_path(src)
        image = Image.open(src)
        mode = image.mode
        W, H = self.get_extents("W")
        W1, H1 = self.get_extents("_")
        W,H = max(W,H,W1,H1), max(W,H, W1, H1)
        image = image.resize((W, H))
        #print 'extent calculted', W,H
        self.texture.blit_buffer(image.tobytes(), colorfmt=img_modes[mode], size=(W,H), pos=(x,y))

    def __init__(self, *largs, **kwargs):
        super(SymbolCoreLabel, self).__init__(*largs, **kwargs)
        self.guiLabel = kwargs['guiLabel']
        self.options['symbol'] = False

    @property
    def markup(self):
        '''Return the text with all the markup splitted::

            >>> MarkupLabel('[b]Hello world[/b]').markup
            >>> ('[b]', 'Hello world', '[/b]')

        '''
        s = re.split('(\[.*?\])', self.label)
        s = [x for x in s if x != '']
        return s

    def _render_real(self):
        lines = self._cached_lines
        options = None
        for line in lines:
            if len(line.words):  # get opts from first line, first word
                options = line.words[0].options
                break
        if not options:  # there was no text to render
            self._render_begin()
            data = self._render_end()
            assert(data)
            if data is not None and data.width > 1:
                self.texture.blit_data(data)
            return

        old_opts = self.options
        render_text = self._render_text
        render_image = self._render_image

        xpad, ypad = options['padding_x'], options['padding_y']
        x, y = xpad, ypad   # pos in the texture
        iw, ih = self._internal_size  # the real size of text, not texture
        w, h = self.size
        halign = options['halign']
        valign = options['valign']
        refs = self._refs
        anchors = self._anchors
        self._render_begin()

        if valign == 'bottom':
            y = h - ih + ypad
        elif valign == 'middle':
            y = int((h - ih) / 2 + ypad)

        # in this list, we collect all the image to be blitted latter on. otherwise self._surface will crush them
        pasted_imgs = list()


        for layout_line in lines:  # for plain label each line has only one str
            lw, lh = layout_line.w, layout_line.h
            x = xpad
            if halign[0] == 'c':  # center
                x = int((w - lw) / 2.)
            elif halign[0] == 'r':  # right
                x = max(0, int(w - lw - xpad))
            layout_line.x = x
            layout_line.y = y
            psp = pph = 0
            for word in layout_line.words:
                options = self.options = word.options
                # the word height is not scaled by line_height, only lh was
                wh = options['line_height'] * word.lh
                # calculate sub/super script pos
                if options['script'] == 'superscript':
                    script_pos = max(0, psp if psp else self.get_descent())
                    psp = script_pos
                    pph = wh
                elif options['script'] == 'subscript':
                    script_pos = min(lh - wh, ((psp + pph) - wh)
                                     if pph else (lh - wh))
                    pph = wh
                    psp = script_pos
                else:
                    script_pos = (lh - wh) / 1.25
                    psp = pph = 0

                if not options.get('symbol',False):
                    if len(word.text):
                        #print 'rendering symbotext', word.text, 'at', x,y+script_pos
                        render_text(word.text, x, y + script_pos)
                else:
                    try:
                        #print 'renderinf symbol img', options['symbol_src'], 'at', x, y+script_pos
                        pasted_imgs.append((options.get('symbol_src'), x ,y + script_pos))
                    except Exception,_exc:
                        Logger.warning('Not able to load symbol: %s'%_exc)
                        render_text(word.text, x, y + script_pos)


                # should we record refs ?
                ref = options['_ref']
                if ref is not None:
                    if not ref in refs:
                        refs[ref] = []
                    refs[ref].append((x, y, x + word.lw, y + wh))

                # Should we record anchors?
                anchor = options['_anchor']
                if anchor is not None:
                    if not anchor in anchors:
                        anchors[anchor] = (x, y)
                x += word.lw
            y += lh

        self.options = old_opts
        # get data from provider
        data = self._render_end()
        assert(data)

        # If the text is 1px width, usually, the data is black.
        # Don't blit that kind of data, otherwise, you have a little black bar.
        if data is not None and data.width > 1:
            self.texture.blit_data(data)
            #Now render all symbol images
            for args in pasted_imgs:
                #print 'here !! ', args
                render_image(*args)

    def _pre_render(self):
        # split markup, words, and lines
        # result: list of word with position and width/height
        # during the first pass, we don't care about h/valign
        self._cached_lines = lines = []
        self._refs = {}
        self._anchors = {}
        clipped = False
        w = h = 0
        uw, uh = self.text_size
        spush = self._push_style
        spop = self._pop_style
        opts = options = self.options
        options['_ref'] = None
        options['_anchor'] = None
        options['script'] = 'normal'
        shorten = options['shorten']
        # if shorten, then don't split lines to fit uw, because it will be
        # flattened later when shortening and broken up lines if broken
        # mid-word will have space mid-word when lines are joined
        uw_temp = None if shorten else uw
        xpad = options['padding_x']
        uhh = (None if uh is not None and options['valign'][-1] != 'p' or
               options['shorten'] else uh)
        options['strip'] = options['strip'] or options['halign'][-1] == 'y'

        for item in self.markup:
            #print 'Prerenderinf markup utem', item, options
            if item == '[b]':
                spush('bold')
                options['bold'] = True
                self.resolve_font_name()
            elif item == '[/b]':
                spop('bold')
                self.resolve_font_name()
            elif item == self.guiLabel.start_symbol:
                #print 'stating symbol in heree'
                spush('symbol')
                options['symbol']=True
            elif item == self.guiLabel.end_symbol:
                #print 'stopping symbol in there'
                spop('symbol')
                options['symbol'] = False
            elif options['symbol']:
                # Check if symbol proposed belongs to current symbol dict. If not, go out of symbol mode
                if item in self.guiLabel.symbols:
                    options['symbol_src'] = self.guiLabel.symbols[item]
                    # Create a single CHAR item, which will be replaced by the picture
                    item="__"
                    opts = copy(options)
                    extents = self.get_cached_extents()
                    opts['space_width'] = extents(' ')[0]
                    w, h, clipped = layout_text(item, lines, (w, h),(uw_temp, uhh), opts, extents, True, False)
                else:
                    options['symbol'] = False
            elif item == '[i]':
                spush('italic')
                options['italic'] = True
                self.resolve_font_name()
            elif item == '[/i]':
                spop('italic')
                self.resolve_font_name()
            elif item[:6] == '[size=':
                item = item[6:-1]
                try:
                    if item[-2:] in ('px', 'pt', 'in', 'cm', 'mm', 'dp', 'sp'):
                        size = dpi2px(item[:-2], item[-2:])
                    else:
                        size = int(item)
                except ValueError:
                    raise
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
            elif item[:5] == '[sub]':
                spush('font_size')
                spush('script')
                options['font_size'] = options['font_size'] * .5
                options['script'] = 'subscript'
            elif item == '[/sub]':
                spop('font_size')
                spop('script')
            elif item[:5] == '[sup]':
                spush('font_size')
                spush('script')
                options['font_size'] = options['font_size'] * .5
                options['script'] = 'superscript'
            elif item == '[/sup]':
                spop('font_size')
                spop('script')
            elif item[:5] == '[ref=':
                ref = item[5:-1]
                spush('_ref')
                options['_ref'] = ref
            elif item == '[/ref]':
                spop('_ref')
            elif not clipped and item[:8] == '[anchor=':
                options['_anchor'] = item[8:-1]
            elif not clipped:
                item = item.replace('&bl;', '[').replace(
                    '&br;', ']').replace('&amp;', '&')
                opts = copy(options)
                extents = self.get_cached_extents()
                opts['space_width'] = extents(' ')[0]
                w, h, clipped = layout_text(item, lines, (w, h),
                    (uw_temp, uhh), opts, extents, True, False)


        if len(lines):  # remove any trailing spaces from the last line
            old_opts = self.options
            self.options = copy(opts)
            w, h, clipped = layout_text('', lines, (w, h), (uw_temp, uhh),
                self.options, self.get_cached_extents(), True, True)
            self.options = old_opts

        if shorten:
            options['_ref'] = None  # no refs for you!
            options['_anchor'] = None
            w, h, lines = self.shorten_post(lines, w, h)
            self._cached_lines = lines
        # when valign is not top, for markup we layout everything (text_size[1]
        # is temporarily set to None) and after layout cut to size if too tall
        elif uh != uhh and h > uh and len(lines) > 1:
            if options['valign'][-1] == 'm':  # bottom
                i = 0
                while i < len(lines) - 1 and h > uh:
                    h -= lines[i].h
                    i += 1
                del lines[:i]
            else:  # middle
                i = 0
                top = int(h / 2. + uh / 2.)  # remove extra top portion
                while i < len(lines) - 1 and h > top:
                    h -= lines[i].h
                    i += 1
                del lines[:i]
                i = len(lines) - 1  # remove remaining bottom portion
                while i and h > uh:
                    h -= lines[i].h
                    i -= 1
                del lines[i + 1:]

        # now justify the text
        if options['halign'][-1] == 'y' and uw is not None:
            # XXX: update refs to justified pos
            # when justify, each line shouldv'e been stripped already
            split = partial(re.split, re.compile('( +)'))
            uww = uw - 2 * xpad
            chr = type(self.text)
            space = chr(' ')
            empty = chr('')

            for i in range(len(lines)):
                line = lines[i]
                words = line.words
                # if there's nothing to justify, we're done
                if (not line.w or int(uww - line.w) <= 0 or not len(words) or
                    line.is_last_line):
                    continue

                done = False
                parts = [None, ] * len(words)  # contains words split by space
                idxs = [None, ] * len(words)  # indices of the space in parts
                # break each word into spaces and add spaces until it's full
                # do first round of split in case we don't need to split all
                for w in range(len(words)):
                    word = words[w]
                    sw = word.options['space_width']
                    p = parts[w] = split(word.text)
                    idxs[w] = [v for v in range(len(p)) if
                               p[v].startswith(' ')]
                    # now we have the indices of the spaces in split list
                    for k in idxs[w]:
                        # try to add single space at each space
                        if line.w + sw > uww:
                            done = True
                            break
                        line.w += sw
                        word.lw += sw
                        p[k] += space
                    if done:
                        break

                # there's not a single space in the line?
                if not any(idxs):
                    continue

                # now keep adding spaces to already split words until done
                while not done:
                    for w in range(len(words)):
                        if not idxs[w]:
                            continue
                        word = words[w]
                        sw = word.options['space_width']
                        p = parts[w]
                        for k in idxs[w]:
                            # try to add single space at each space
                            if line.w + sw > uww:
                                done = True
                                break
                            line.w += sw
                            word.lw += sw
                            p[k] += space
                        if done:
                            break

                # if not completely full, push last words to right edge
                diff = int(uww - line.w)
                if diff > 0:
                    # find the last word that had a space
                    for w in range(len(words) - 1, -1, -1):
                        if not idxs[w]:
                            continue
                        break
                    old_opts = self.options
                    self.options = word.options
                    word = words[w]
                    # split that word into left/right and push right till uww
                    l_text = empty.join(parts[w][:idxs[w][-1]])
                    r_text = empty.join(parts[w][idxs[w][-1]:])
                    left = LayoutWord(word.options,
                        self.get_extents(l_text)[0], word.lh, l_text)
                    right = LayoutWord(word.options,
                        self.get_extents(r_text)[0], word.lh, r_text)
                    left.lw = max(left.lw, word.lw + diff - right.lw)
                    self.options = old_opts

                    # now put words back together with right/left inserted
                    for k in range(len(words)):
                        if idxs[k]:
                            words[k].text = empty.join(parts[k])
                    words[w] = right
                    words.insert(w, left)
                else:
                    for k in range(len(words)):
                        if idxs[k]:
                            words[k].text = empty.join(parts[k])
                line.w = uww
                w = max(w, uww)

        self._internal_size = w, h
        if uw:
            w = uw
        if uh:
            h = uh
        if h > 1 and w < 2:
            w = 2
        if w < 1:
            w = 1
        if h < 1:
            h = 1
        return int(w), int(h)


class SymbolLabel(Label):
    start_symbol = StringProperty('[s]')
    end_symbol = StringProperty('[/s]')
    symbols = DictProperty()

    def Otexture_update(self, *largs):
        '''Force texture recreation with the current Label properties.

        After this function call, the :attr:`texture` and :attr:`texture_size`
        will be updated in this order.
        '''
        self.texture = None

        if (not self._label.text or (self.halign[-1] == 'y' or self.strip) and
            not self._label.text.strip()):
            self.texture_size = (0, 0)
            self.refs, self._label._refs = {}, {}
            self.anchors, self._label._anchors = {}, {}
        else:
            text = self._label.text
            # we must strip here, otherwise, if the last line is empty,
            # markup will retain the last empty line since it only strips
            # line by line within markup
            if self.halign[-1] == 'y' or self.strip:
                text = text.strip()
            self._label.text = ''.join(('[color=',  get_hex_from_color(self.color), ']', text, '[/color]'))
            self._label.refresh()
            # force the rendering to get the references
            if self._label.texture:
                self._label.texture.bind()
            self.refs = self._label.refs
            self.anchors = self._label.anchors
            texture = self._label.texture
            if texture is not None:
                self.texture = self._label.texture
                self.texture_size = list(self.texture.size)


###################

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
            self._label = SymbolCoreLabel(guiLabel=self,**dkw)
