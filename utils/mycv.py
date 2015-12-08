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

def imgwrapper(obj):
    "If I am a pure cv2 img, then wrap me around Image class"
    if hasattr(obj,'_ocvimg'):
        return obj
    return Image.fromobj(obj)

def imgunwrap(obj):
    if hasattr(obj,'_ocvimg'):
        return obj._ocvimg
    return obj

def imginplace(func):
    def wrapped(self, inplace= False, *args, **kwargs):
        res = func(self, *args, **kwargs)
        if inplace:
            self._ocvimg = res
            return self
        else:
            return imgwrapper(res)
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
        img = cv2.addWeighted(self._ocvimg, w1, imgwrapper(other), w2)
        if inplace:
            self._ocvimg = img
            return self
        return Image.fromobj(img)

    def convert(self,mode):
        return imgwrapper(cv2.cvtColor(self._ocvimg, mode))

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
        return imgwrapper(cv2.threshold(self._ocvimg, thresh, maxval, mode))

    def __and__(self, other,**kwargs):
        return imgwrapper(cv2.bitwise_and(self._ocvimg, imgunwrap(other), **kwargs))

    def __or__(self, other,**kwargs):
        return imgwrapper(cv2.bitwise_or(self._ocvimg, imgunwrap(other), **kwargs))

    def __not__(self,**kwargs):
        return imgwrapper(cv2.bitwise_not(self._ocvimg), **kwargs)

    def __add__(self, other):
        return imgwrapper(cv2.add(self._ocvimg, imgunwrap(other)))

    def range_filter(self, low,up, inplace=False):
        "Equivalent to cv2.Inrange"
        img =  cv2.inRange(self._ocvimg,low,up)
        if inplace:
            self._ocvimg = img
            return self
        return imgwrapper(img)

    def show(self, displayname = 'image'):
        cv2.imshow(displayname,self._ocvimg)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def findContours(self,return_type = cv2.RETR_TREE, method = cv2.CHAIN_APPROX_SIMPLE):
        contours, hierarchy = cv2.findContours(self._ocvimg, return_type, method)
        return [Contour.fromobj(c) for c in contours], hierarchy

    def drawContours(self, contoursList, color=(0,255,0), width=3):
        clist = [Contour.unwrap(c) for c in contoursList]
        cv2.drawContours(self._ocvimg, clist, -1, color, width)

    def drawContour(self, contour, color, width):
        self.drawContours(self,[contour], color, width)

class Contour:
    _ocvcontour = None

    @classmethod
    def wrapper(cls, obj):
        if hasattr(obj, '_ocvcontour'):
            return obj
        return Contour.fromobj(obj)

    @classmethod
    def unwrap(cls,obj):
        if hasattr(obj, '_ocvcontour'):
            return obj._ocvcontour
        return obj

    @classmethod
    def fromobj(cls, cvc):
        c= Contour()
        c._ocvcontour = cvc

    @property
    def moments(self):
        return cv2.moments(self._ocvcontour)

    @property
    def area(self):
        return cv2.contourArea(self._ocvcontour)

    @property
    def perimeter(self):
        return cv2.arcLeength(self._ocvcontour,True)

    def approx(self, epsilon_ratio):
        eps = epsilon_ratio * self.perimeter
        return cv2.approxPolyDP(self._ocvcontour,eps,True)

    @property
    def convex(self):
        return cv2.isContourConvex(self._ocvcontour)

    @property
    def bounding_rect(self):
        return cv2.boundingRect(self._ocvcontour)

    @property
    def bounding_rotated_rect(self):
        return cv2.minAreaRecf(self._ocvcontour)

    @property
    def enclosing_circle(self):
        return cv2.minEnclosingCircle(self._ocvcontour)

    @property
    def fit_ellipse(self):
        return cv2.fitEllipse(self._ocvcontour)

    @property
    def aspect_ratio(self):
        x,y,w,h = self.bounding_rect
        return float(w)/h

    @property
    def extent(self):
        x,y,w,h = self.bounding_rect
        return float(self.area) / w*h

    @property
    def extremum(self):
        "Return leftmost, rightmost, topmost & bottommost point in contours"
        cnt = self._ocvcontour
        leftmost = tuple(cnt[cnt[:,:,0].argmin()][0])
        rightmost = tuple(cnt[cnt[:,:,0].argmax()][0])
        topmost = tuple(cnt[cnt[:,:,1].argmin()][0])
        bottommost = tuple(cnt[cnt[:,:,1].argmax()][0])
        return (leftmost, rightmost, topmost, bottommost)


class Video(Image):
    _ocvvideo = None

    def capture(self):
        self._ocvvideo = cv2.VideoCapture(0)

    def read(self):
        return self._ocvvideo.read()
