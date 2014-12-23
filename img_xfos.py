__author__ = 'opq'

from PIL import Image, ImageOps


def grey(img):
    print 'entry:', img.size, img.mode
    gimg =  ImageOps.grayscale(img)
    print 'output', gimg.size, gimg.mode
    return gimg

def grey2(img):
    return img.convert('LA')

def grey_opencv(img):
    #Convert PIL to OpenCV
    import numpy
    oimage = numpy.array(img)
    #convert rgb to bgr
    oimage = oimage[:,:,::-1].copy()
    import cv2
    gimage = cv2.cvtColor(oimage, cv2.COLOR_BGR2GRAY)
    return Image.fromarray(gimage)

def v_flip(img):
    return img.transpose(Image.FLIP_TOP_BOTTOM)

def h_flip(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)

def opacer(alpha):
    def inner(img):
        img.putalpha(int(alpha * 255))
        return img
    return inner

def identity(img):
    return img

xfos = {
    'Identity': identity,
    'HFlip': h_flip,
    'VFlip': v_flip,
    'Grey': grey,
    'grey2': grey2,
    'grey_opencv': grey_opencv,
}

img_modes = {
    'RGB' : 'rgb',
    'RGBA': 'rgba',
    'L': 'luminance',
    'LA': 'luminance_alpha'
}