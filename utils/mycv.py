__author__ = 'opq'
import cv2
import numpy as np

BORDER_OPTIONS = {
    'REPLICATE': cv2.BORDER_REPLICATE,#Last element is replicated throughout, like this: aaaaaa|abcdefgh|hhhhhhh
    'REFLECT': cv2.BORDER_REFLECT,#Border will be mirror reflection of the border elements, like this : fedcba|abcdefgh|hgfedcb
    'DEFAULT': cv2.BORDER_DEFAULT,# Same as above, but with a slight change, like this : gfedcb|abcdefgh|gfedcba
    'CONSTANT': cv2.BORDER_CONSTANT,#Adds a constant colored border. The value should be given as next argument.
    'WRAP': cv2.BORDER_WRAP,

}

def wrapper(obj):
    "If I am a pure cv2 img, then wrap me around Image class"
    if hasattr(obj,'_ocvimg'):
        return obj
    return Image.fromobj(obj)

def unwrap(obj):
    if hasattr(obj,'_ocvimg'):
        return obj._ocvimg
    return obj

def inplace(func):
    def wrapped(self, inplace= False, *args, **kwargs):
        res = func(self, *args, **kwargs)
        if inplace:
            self._ocvimg = res
            return self
        else:
            return wrapper(res)
    return wrapped



class Image(object):
    _ocvimg = None
    name = "Image"
    color_mode = None

    def __init__(self, path=None):
        if path:
            self_ocvimg = cv2.imread(path)
        self.color_mode = 'BGR'

    def split(self):
        return cv2.split(self._ocvimg)

    def show(self):
        cv2.imshow(self.name,self._ocvimg)
        cv2.waitKey(0)

    @classmethod
    def frommerge(self, components):
        ocvimg = cv2.merge(components)
        return Image.fromobj(ocvimg)

    @classmethod
    def fromobj(cls, ocvimg):
        img = cls()
        img._ocvimg = ocvimg
        return img

    def __getitem__(self, item):
        return self._ocvimg.__getitem__(item)

    def __setitem(self, item, value):
        return self._ocvimg.__setitem__(item, value)

    def addborder(self, top, bottom, left,right, btype, inplace= False, **kwargs):
        ""
        img = cv2.copyMakeBorder(top,bottom,left, right, btype, **kwargs)
        if inplace:
            self._ocvimg = img
            return self
        return Image.fromobj(img)

    def blend(self, other, w1,w2, inplace = False):
        "Similar to cv2.addWeighted (img1,w1,img2,w2)"
        img = cv2.addWeighted(self._ocvimg,w1,wrapper(other),w2)
        if inplace:
            self._ocvimg = img
            return self
        return Image.fromobj(img)

    def convert(self,mode):
        return wrapper(cv2.cvtColor(self._ocvimg, mode))

    def colorconvert(self, dstmode, srcmode=None, inplace = False):
        if srcmode is None:
            srcmode = self.color_mode
        attr = getattr(cv2, 'COLOR_%s2%s'%(srcmode.upper(),dstmode.upper()))
        print attr, 'COLOR_%s2%s'%(srcmode.upper(),dstmode.upper())
        img =  cv2.cvtColor(self._ocvimg,attr)
        if inplace:
            self._ocvimg = img
            self.color_mode = dstmode
            return self
        else:
            IMG = Image.fromobj(img)
            IMG.color_mode = dstmode
            return IMG


    def threshold(self, thresh, maxval, mode):
        return wrapper(cv2.threshold(self._ocvimg,thresh, maxval, mode))

    def __and__(self, other,**kwargs):
        return wrapper(cv2.bitwise_and(self._ocvimg,unwrap(other), **kwargs))

    def __or__(self, other,**kwargs):
        return wrapper(cv2.bitwise_or(self._ocvimg, unwrap(other),**kwargs))

    def __not__(self,**kwargs):
        return wrapper(cv2.bitwise_not(self._ocvimg),**kwargs)

    def __add__(self, other):
        return wrapper(cv2.add(self._ocvimg, unwrap(other)))

    def range_filter(self, low,up, inplace=False):
        "Equivalent to cv2.Inrange"
        img =  cv2.inRange(self._ocvimg,low,up)
        if inplace:
            self._ocvimg = img
            return self
        return wrapper(img)


class Video(Image):
    _ocvvideo = None

    def capture(self):
        self._ocvvideo = cv2.VideoCapture(0)

    def read(self):
        return self._ocvvideo.read()
