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

THRESHOLD_OPTIONS = {
    'BINARY' : cv2.THRESH_BINARY,
    'BINARY_INV': cv2.THRESH_BINARY_INV,
    'TRUNC': cv2.THRESH_TRUNC,
    'TOZERO': cv2.THRESH_TOZERO,
    'TOZERO_INV': cv2.THRESH_TOZERO_INV
}

TEMPLATE_MATCHING_OPTIONS = {
    'CCOEFF': cv2.TM_CCOEFF,
    'CCOEFF_NORMED': cv2.TM_CCOEFF_NORMED,
    'CCORR': cv2.TM_CCORR,
    "CCORR_NORMED": cv2.TM_CCORR_NORMED,
    'SQDIFF': cv2.TM_SQDIFF,
    'SQDIFF_NORMED': cv2.TM_SQDIFF_NORMED,

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


def img_in_placer(func):
    def called(self, in_place=False, *args, **kwargs):
        res = func(self, *args, **kwargs)
        if in_place:
            self._ocvimg = res
            return self
        else:
            return imgwrapper(res)
    return called


class Image(object):
    _ocvimg = None
    name = "Image"
    color_mode = None


########################################################################################################################
#   Standard Functions                                                                                                  #
########################################################################################################################

    def _get_size(self):
        h, w = self._ocvimg.shape[:2]
        return int(w), int(h)

    def _set_size(self, size, interpolation = cv2.INTER_LINEAR):
        self._ocvimg = cv2.resize(self._ocvimg, size, interpolation=interpolation)

    size = property(_get_size, _set_size)

    def __init__(self, path=None):
        obj = cv2.imread(path)
        self._ocvimg = obj
        self.color_mode = 'BGR'

    def split(self):
        return [Image.fromobj(x) for x in cv2.split(self._ocvimg)]

    def show(self):
        cv2.imshow(self.name,self._ocvimg)
        cv2.waitKey(0)

    def copy(self):
        copy = self._ocvimg.copy()
        return Image.fromobj(copy)

    @classmethod
    def frommerge(self, components):
        components = [imgunwrap(x) for x in components]
        ocvimg = cv2.merge(components)
        return Image.fromobj(ocvimg)

    @classmethod
    def fromobj(cls, ocvimg):
        img = cls()
        img._ocvimg = ocvimg
        return img

    def __getitem__(self, item):
        return self._ocvimg.__getitem__(item)

    def __setitem__(self, item, value):
        return self._ocvimg.__setitem__(item, value)

    def _get_num_channels(self):
        shape = self._ocvimg.shape
        if len(shape) == 2:
            return 1
        if len(shape) == 3:
            return int(shape[-1])

    channel = property(_get_num_channels)

    def show(self, displayname = 'image'):
        cv2.imshow(displayname,self._ocvimg)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

########################################################################################################################
#   Draw Img Functions                                                                                                  #
########################################################################################################################
    def draw_line(self, start, end, color, thickness=1, lineType=8, shift= 0):
        "LineType can be 8, 4, or AA for antialiased"
        if str(lineType).upper()=="AA":
            lineType = cv2.CV_AA
        cv2.line(self._ocvimg, start,end, color, thickness, lineType, shift)

    def draw_rectangle(self, top_left, bottom_right, color, thickness=1,lineType=8, shift= 0):
        "LineType can be 8, 4, or AA for antialiased"
        if str(lineType).upper()=="AA":
            lineType = cv2.CV_AA
        cv2.rectangle(self._ocvimg, top_left, bottom_right, color, thickness, lineType,shift)

    def draw_circle(self, center, radius, color, thickness=1, lineType=8, shift=0):
        "LineType can be 8, 4, or AA for antialiased"
        if str(lineType).upper()=="AA":
            lineType = cv2.CV_AA
        cv2.circle(self._ocvimg, center, radius, color, thickness,lineType, shift)

    def draw_ellipse(self, axes, angle, startAngle, endAngle, color, thickness=1, lineType=8, shift=0):
        "LineType can be 8, 4, or AA for antialiased"
        if str(lineType).upper()=="AA":
            lineType = cv2.CV_AA
        cv2.ellipse(self._ocvimg, axes, angle, startAngle, endAngle, color, thickness, lineType, shift)

########################################################################################################################
#   Core Img Functions                                                                                                  #
########################################################################################################################

    @img_in_placer
    def add_border(self, top, bottom, left,right, btype='DEFAULT', inplace= False, **kwargs):
        ""
        if btype in BORDER_OPTIONS:
            btype = BORDER_OPTIONS[btype]
        return cv2.copyMakeBorder(top,bottom,left, right, btype, **kwargs)

    def blend(self, other, w1, w2, inplace = False):
        "Similar to cv2.addWeighted (img1,w1,img2,w2)"
        img = cv2.addWeighted(self._ocvimg, w1, imgwrapper(other), w2)
        if inplace:
            self._ocvimg = img
            return self
        return Image.fromobj(img)

    def convert_color(self, dstmode, srcmode=None, inplace=False):
        if srcmode is None:
            srcmode = self.color_mode
        attr = getattr(cv2, 'COLOR_%s2%s'%(srcmode.upper(),dstmode.upper()))
        img = cv2.cvtColor(self._ocvimg,attr)
        if inplace:
            self._ocvimg = img
            self.color_mode = dstmode
            return self
        else:
            IMG = Image.fromobj(img)
            IMG.color_mode = dstmode
            return IMG

    def threshold(self, thresh, maxval, mode, otsu=False):
        if mode in THRESHOLD_OPTIONS:
            mode = THRESHOLD_OPTIONS[mode]
        if otsu:
            mode += cv2.THRESH_OTSU
            thresh = 0
        ret, thres = cv2.threshold(self._ocvimg, thresh, maxval, mode)
        return ret, imgwrapper(thres)

    def __and__(self, other,**kwargs):
        return imgwrapper(cv2.bitwise_and(self._ocvimg, imgunwrap(other), **kwargs))

    def __or__(self, other,**kwargs):
        return imgwrapper(cv2.bitwise_or(self._ocvimg, imgunwrap(other), **kwargs))

    def __not__(self,**kwargs):
        return imgwrapper(cv2.bitwise_not(self._ocvimg), **kwargs)

    def __add__(self, other):
        return imgwrapper(cv2.add(self._ocvimg, imgunwrap(other)))

    @img_in_placer
    def range_filter(self, low,up, inplace=False):
        "Equivalent to cv2.Inrange"
        return cv2.inRange(self._ocvimg,low,up)

########################################################################################################################
#   Contours  Functions                                                                                                  #
########################################################################################################################

    def find_contours(self,return_type = cv2.RETR_TREE, method = cv2.CHAIN_APPROX_SIMPLE):
        res = cv2.findContours(self._ocvimg, return_type, method)
        _, contours, hierarchy = res
        return [Contour.fromobj(c) for c in contours], hierarchy

    def draw_contours(self, contoursList, color=(0,255,0), width=3):
        clist = [Contour.unwrap(c) for c in contoursList]
        cv2.drawContours(self._ocvimg, clist, -1, color, width)

    def draw_contour(self, contour, color, width):
        self.draw_contours([contour], color, width)

    def in_range(self, lower, upper):
        return cv2.inRange(self._ocvimg, lower, upper)

########################################################################################################################
#   Transforamtion Functions                                                                                                  #
########################################################################################################################

    def __and__(self, other,mask=None):
        if mask is None:
            return cv2.bitwise_and(self._ocvimg, imgunwrap(other))
        return cv2.bitwise_and(self._ocvimg, imgunwrap(other), mask)

    def __or__(self, other,mask=None):
        if mask is None:
            return cv2.bitwise_or(self._ocvimg, imgunwrap(other))
        return cv2.bitwise_or(self._ocvimg, imgunwrap(other), mask)

    def __xor__(self, other,mask=None):
        if mask is None:
            return cv2.bitwise_xor(self._ocvimg, imgunwrap(other))
        return cv2.bitwise_xor(self._ocvimg, imgunwrap(other), mask)

    @img_in_placer
    def apply_affine_transfo(self, xfo, in_place = False):
        rows,cols = self.size
        return Image.fromobj(cv2.warpAffine(self._ocvimg,xfo, (cols,rows)))

    @img_in_placer
    def apply_perspective_transfo(self, xfo, in_place = False):
        rows,cols = self.size
        return Image.fromobj(cv2.warpPerspective(self._ocvimg,xfo, (cols,rows)))

    def rotate(self,  angle, center=None, in_place = False):
        if center is None:
            h,w = self._ocvimg.shape[:2]
            center = w/2, h/2
        M = cv2.getRotationMatrix2D(center, angle, 1)
        return self.apply_transfo(M, in_place)

    def affine(self, src,dst, in_place=False):
        "Where src & dst are list of points (src is ttransformed in dst"
        M = cv2.getAffineTransform(src, dst)
        return self.apply_transfo(M, in_place)

    def perspective(self, src,dst, in_place=False):
        "Same as affine, for perspective Xfo.. Dst_size is the size wanted for dst image "
        M = cv2.getPerspectiveTransform(src, dst)
        return self.apply_perspective_transfo(M, in_place)

    @img_in_placer
    def filter2D(self,kernel, depth=-1):
        return cv2.filter2D(self._ocvimg,depth, kernel)

    @img_in_placer
    def blur(self, kernel_size=(5,5)):
        return cv2.blur(self._ocvimg, kernel_size)

    @img_in_placer
    def median_blur(self, size=5):
        return cv2.medianBlur(size)

    @img_in_placer
    def gaussian_blur(self, kernel_size=(5,5), depth=0):
        return cv2.GaussianBlur(self._ocvimg, kernel_size, depth)

    @img_in_placer
    def bilateral_filter(self, filter_size=5, sigma_color=75, sigma_space=75, border_type= BORDER_OPTIONS['DEFAULT']):
        return cv2.bilateralFilter(self._ocvimg,filter_size, sigma_color, sigma_space, border_type)


########################################################################################################################
#   Mrophology Functions                                                                                                  #
########################################################################################################################

    @img_in_placer
    def erode(self, kernel, iterations=1):
        return cv2.erode(self._ocvimg, kernel, iterations)

    @img_in_placer
    def dilate(self, kernel, iterations=1):
        return cv2.dilate(self._ocvimg, kernel, iterations)

    @img_in_placer
    def opening(self, kernel):
        "Erosion followed by dilation"
        return cv2.morphologyEx(self._ocvimg, cv2.MORPH_OPEN, kernel)

    @img_in_placer
    def closing(self, kernel):
        "Dilation followed by erosion"
        return cv2.morphologyEx(self._ocvimg, cv2.MORPH_CLOSE, kernel)

    @img_in_placer
    def morph_gradient(self, kernel):
        "Difference between erosion & dilation"
        return cv2.morphologyEx(self._ocvimg, cv2.MORPH_GRADIENT, kernel)

    @img_in_placer
    def top_hat(self, kernel):
        "Difference between image & its opening"
        return cv2.morphologyEx(self._ocvimg, cv2.MORPH_TOPHAT, kernel)

    @img_in_placer
    def black_hat(self, kernel):
        "Difference between image & its closing"
        return cv2.morphologyEx(self._ocvimg, cv2.MORPH_BLACKHAT, kernel)

    @img_in_placer
    def transpose(self):
        return cv2.transpose(self._ocvimg)

    def __add__(self, other):
        return Image.fromobj(cv2.add(self._ocvimg,imgunwrap(other)))

    def __eq__(self, other):
        return cv2.compare(self._ocvimg, imgunwrap(other), cv2.CMP_EQ)

    def __gt__(self, other):
        return cv2.compare(self._ocvimg, imgunwrap(other), cv2.CMP_GT)

    def __ge__(self, other):
        return cv2.compare(self._ocvimg, imgunwrap(other), cv2.CMP_GE)

    def __lt__(self, other):
        return cv2.compare(self._ocvimg, imgunwrap(other), cv2.CMP_LT)

    def __le__(self, other):
        return cv2.compare(self._ocvimg, imgunwrap(other), cv2.CMP_LE)

    def __ne__(self, other):
        return cv2.compare(self._ocvimg, imgunwrap(other), cv2.CMP_NE)

    @img_in_placer
    def flip(self, horizontal=False, vertical=False):
        if vertical:
            if horizontal:
                code = -1
            else:
                code = 0
        else:
            if horizontal:
                code = 1
            else:
                return self._ocvimg
        return cv2.flip(self._ocvimg, code)

    @img_in_placer
    def laplacian(self, depth= cv2.CV_64F, ksize=1, scale=1, delta=0, border_type='DEFAULT'):
        return cv2.laplacian(self._ocvimg, depth, ksize, scale, delta, border_type)

########################################################################################################################
#   Edge Detections                                                                                                  #
########################################################################################################################


    @img_in_placer
    def canny(self, threshold1, threshold2, apertureSize=3, L2gradient= False):
        return cv2.Canny(self._ocvimg, threshold1, threshold2, apertureSize, L2gradient)

########################################################################################################################
#   Pyramid Functions                                                                                                  #
########################################################################################################################

    @img_in_placer
    def lower_pyramid(self):
        return cv2.pyrDown(self._ocvimg)

    @img_in_placer
    def upper_pyramid(self):
        return cv2.pyrUp(self._ocvimg)

########################################################################################################################
#   Histogram Functions                                                                                                  #
########################################################################################################################

    def histogram(self, channel_index=0, mask= None, histSize=[256], ranges=[0,256]):
        if mask:
            mask = imgunwrap(mask)
        return cv2.calcHist([self._ocvimg],[channel_index], mask, histSize, ranges)

    @img_in_placer
    def histogram_equalization(self):
        return cv2.equalizeHist(self._ocvimg)

    @img_in_placer
    def adaptive_histogram_equalization(self, clipLimit=2.0, tileGridSize=(8,8)):
        clahe = cv2.createCLAGE(clipLimit=clipLimit, tileGridSize=tileGridSize)
        return clahe.apply(self._ocvimg)

    def histogram2D(self):
        hsv = self.convert_color('HSV')
        return cv2.calvHist([hsv], [0,1], None, [180,256], [0,180,0,256])

########################################################################################################################
#   Template Matching Functions                                                                                                  #
########################################################################################################################

    @img_in_placer
    def match(self, template, method = 'CCOEFF_NORMED'):
        return cv2.matchTemplate(self._ocvimg, template, method)

########################################################################################################################
#   Hough Transform Functions                                                                                                  #
########################################################################################################################
    def hough_lines(self, return_as_line = True, from_edges=False, rho=1, theta=np.pi/180, threshold=200):
        """If from_edges is True, then image is already ready canny edges. Otherwise, compute them.
        if return_as_line is True, return a list of coord. Otherwise, return rho,theta list from cv2 function"""

        target = self._ocvimg
        if not from_edges:
            gray = self.convert_color('GRAY')
            target = gray.canny(50,150)
        lines = cv2.HoughLines(target, rho, theta, threshold)
        if not return_as_line:
            return lines
        res = []
        for line in lines:
            rho,theta = line[0]
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a*rho
            y0 = b*rho
            x1 = int(x0 + 1000*(-b))
            y1 = int(y0 + 1000*(a))
            x2 = int(x0 - 1000*(-b))
            y2 = int(y0 - 1000*(a))
            res.append((x1,y1,x2,y2))
        return res

    def probabilistic_hough_lines(self,from_edge=False, rho=1, theta=np.pi/180, threshold=100, minLineLength=100, maxLineGap=10):
        target = self._ocvimg
        if not from_edge:
            gray = self.convert_color('GRAY')
            target = gray.canny(50,150)
        lines = cv2.HoughLinesP(target, rho, theta, threshold, minLineLength, maxLineGap)
        res = [line[0] for line in lines]
        return res

    def hough_circles(self, dp, minDist, param1=100, param2=100, minRadius=0, maxRadius=0):
        "Return circles in a form of a list of (Center,radius) couple"
        circles = cv2.HoughCircles(self._ocvimg, cv2.HOUGH_GRADIENT, dp, minDist, param1, param2, minRadius, maxRadius)
        circles = np.uint16(np.around(circles))
        res= list()
        for i in circles[0,:]:
            center =  i[0], i[1]
            radius = i[2]
            res.append((center, radius))
        return res

########################################################################################################################
#   Features Detections                                                                                                #
########################################################################################################################

    @img_in_placer
    def harris_corner(self, block_size=2, ksize=2, k=0.04):
        return cv2.cornerHarris(self._ocvimg,block_size, ksize, k)


    def features(self,num, qualityLevel=0.01, minDistance=10):
        return cv2.goodFeaturesToTrack(self._ocvimg, num, qualityLevel, minDistance)

    def fast_keypoints(self, mask= None):
        fast= cv2.FastFeatureDetector_create()
        return fast.detectAndCompute(self._ocvimg,mask)

    def orb_keypoints(self, mask=None):
        orb = cv2.ORB_create()
        return orb.detectAndCompute(self._ocvimg, mask)

    def draw_keypoints(self, kp, rich=False, color=(0,255,0), thickness=1):
        flags= 0
        if rich:
            flags = cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS
        cv2.drawKeyPoints(self._ocvimg, kp, flags, color, thickness)

    @img_in_placer
    def draw_matches(self, other, num=10):
        kp1, des1 = self.orb_keypoints()
        kp2, des2 = other.orb_keypoints()
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck = True)
        matches = bf.match(des1, des2)
        matches = sorted(matches, key = lambda x: x.distance)
        return cv2.drawMatches(self._ocvimg, kp1, imgunwrap(other), kp2, matches[:num], flags=2)


class Contour:
    _ocvcontour = None

    @classmethod
    def wrapper(cls, obj):
        if hasattr(obj, '_ocvcontour'):
            return obj
        return Contour.fromobj(obj)

    @classmethod
    def unwrap(cls, obj):
        if hasattr(obj, '_ocvcontour'):
            return obj._ocvcontour
        return obj

    @classmethod
    def fromobj(cls, cvc):
        c = Contour()
        c._ocvcontour = cvc
        return c

    @property
    def convex(self):
        return cv2.isContourConvex(self._ocvcontour)

    @property
    def moments(self):
        return cv2.moments(self._ocvcontour)

    @property
    def area(self):
        return cv2.contourArea(self._ocvcontour)

    @property
    def perimeter(self):
        return cv2.arcLength(self._ocvcontour,True)

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

    def collipe_point(self,point):
        "return 1 if point is inside self, -1 if not and 0 if on the contour"
        return cv2.PointPolygonTest(self._ocvcontour, point, False)

    def distance_to_point(self, point):
        return cv2.PointPolygonTest(self._ocvcontour, point, True)

    def compare_to(self, other, method=1):
        "The less the return, the more similar the shape are"
        obj = Contour.unwrap(other)
        return cv2.matchShapes(self._ocvcontour,obj,method,0)

    @property
    def centroid(self):
        M = self.moments
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])
        return cx,cy


class StructuringElement:
    def __init__(self, se_type, size):
        morph_type = getattr(cv2, 'MORPH_%s'%se_type.upper())
        self._ocvse = cv2.getStructuringElement(morph_type,size)

class Video(Image):
    _ocvvideo = None

    def capture(self):
        self._ocvvideo = cv2.VideoCapture(0)

    def read(self):
        return self._ocvvideo.read()
