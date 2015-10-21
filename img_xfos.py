__author__ = 'opq'
#This library is a list of function, taking a PIL Image and sending another one

from PIL import Image, ImageOps

__all__ =[
    'grey','v_flip','h_flip','opacer','identity','redify', 'perspective_transform',
    'hue_transformer',
]

def hue_transformer(img,hue=None):
#    def inner(img):
    rgb = img.split()
    r= rgb[0]
    img = img.convert('HSV')
    hsv= img.split()
    h= hsv[0]
    print r.getdata()
    print h.getdata()
    return img
#    return inner

def perspective_transform(size, points):
    #Points are list of 4 points and their corresponding target when transformed

    w, h = size
    points_src = [[0,0],[w,0],[0,h],[w, h]]

    points_dst = [[w*points[i], h*points[i+1]] for i in range(0, len(points), 2)]

    import cv2
    import numpy as np
    def inner(img):
        #First transform pil to cv2
        img = Pil2OCV(img)
        rows, cols, ch = img.shape

        #pts1 = np.float32([[56,65],[368,52],[28,387],[389,390]])
        #pts2 = np.float32([[0,0],[300,0],[0,300],[300,300]])

        pts1 = np.float32(points_src)
        pts2 = np.float32(points_dst)
        M = cv2.getPerspectiveTransform(pts1,pts2)

        dst = cv2.warpPerspective(img, M, (rows, cols))

        return OCV2Pil(dst)
    return inner

def grey(img):
    gimg =  ImageOps.grayscale(img)
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

def redify(img):
    IMG = Pil2OCV(img)
    IMG[:,:,1] = 0
    IMG[:,:,0] = 0
    return OCV2Pil(IMG)

def Pil2OCV(img):
    import numpy
    return numpy.array(img)

def OCV2Pil(img):
    return Image.fromarray(img)

xfos = {
    'Identity': identity,
    'HFlip': h_flip,
    'VFlip': v_flip,
    'Grey': grey,
    'grey2': grey2,
    'grey_opencv': grey_opencv,
    'perpective': perspective_transform,
    'hue_transformer': hue_transformer
}

img_modes = {
    'RGB' : 'rgb',
    'RGBA': 'rgba',
    'L': 'luminance',
    'LA': 'luminance_alpha'
}