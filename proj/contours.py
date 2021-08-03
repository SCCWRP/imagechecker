import numpy as np
#from pandas import Series, DataFrame, isnull, concat
from scipy.spatial import ConvexHull, convex_hull_plot_2d
from numpy import random, nanmax, nanmin, argmax, unravel_index
from numpy.linalg import norm
from scipy.spatial.distance import pdist, squareform
from scipy.ndimage import distance_transform_edt
from copy import deepcopy

import time, cv2
import tensorflow as tf


class Object_Detector():
    def __init__(self, model_path):
        self.__load_model(model_path)
        print('model loaded')

    def __load_model(self, model_path):
        self.detection_graph = tf.Graph()
        with self.detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(model_path, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

        config = tf.ConfigProto()
        #config.gpu_options.allow_growth= True

        with self.detection_graph.as_default():
            self.sess = tf.Session(config=config, graph=self.detection_graph)
            self.image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')
            self.detection_boxes = self.detection_graph.get_tensor_by_name('detection_boxes:0')
            self.detection_scores = self.detection_graph.get_tensor_by_name('detection_scores:0')
            self.detection_classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
            self.num_detections = self.detection_graph.get_tensor_by_name('num_detections:0')

        # load label_dict
        self.label_dict = {1: 'fish'}
        
        # warmup
        self.detect_image(np.ones((600, 600, 3)))

    def detect_image(self, image_np, score_thr=0.5, print_time=False):
        image_w, image_h = image_np.shape[1], image_np.shape[0]
    
        # Actual detection.
        t = time.time()
        (boxes, scores, classes, num) = self.sess.run(
          [self.detection_boxes, self.detection_scores, self.detection_classes, self.num_detections],
          feed_dict={self.image_tensor: np.expand_dims(image_np, axis=0)})
        if print_time:
            print('detection time :', time.time()-t)
        # Visualization of the results of a detection.
        boxes = boxes[scores>score_thr]
        boxes_dict = dict()
        for i, box in enumerate(boxes):
            boxes_dict[i] = [float(x) for x in box]
            top_left = (int(box[1]*image_w), int(box[0]*image_h))
            bottom_right = (int(box[3]*image_w), int(box[2]*image_h))
            cv2.rectangle(image_np, top_left, bottom_right, (0,255,0), 3)
            cv2.putText(image_np, "{}_{}".format(self.label_dict[int(classes[0,i])], i), top_left, cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        return image_np, boxes_dict




class Contour:
    def __init__(self, points, original_image, output_photo_path, detector):
        "Original image should be the numpy array version, not the path to the image"
        self.points = points
        self._original_image = original_image
        self._output_photo_path = output_photo_path
        self.cm_pixel_ratio = 1 # default. can be set later
        self._fish_detector = detector

        self._max_x = nanmax([x[0] for x in self.points])
        self._max_y = nanmax([y[1] for y in self.points])
        self._min_x = abs(nanmin([x[0] for x in self.points]))
        self._min_y = abs(nanmin([y[1] for y in self.points]))
        
        return None

    def containsOysters(self, path, detector):
        pass
    
    def containsFish(self):
        im = cv2.cvtColor(self._original_image, cv2.COLOR_BGR2RGB)
        img_, boxes = self._fish_detector.detect_image(
            im[self._min_x:self._max_x, self._min_y:self._max_y], score_thr=0.4
        )
        return True if len(boxes) > 0 else False
    
    def isCircle(self):
        A = self.getArea()
        L = self.getLength()
        return True if (A * 0.9 < 3.14*(L/2)**2 < A * 1.1) else False

    def markBoundingBox(self):
        
        # top line
        cv2.line(self._original_image, (self._min_x, self._min_y), (self._max_x, self._min_y), (0,255,0), 3)
        
        # left border
        cv2.line(self._original_image, (self._min_x, self._min_y), (self._min_x, self._max_y), (0,255,0), 3)
        
        # right border
        cv2.line(self._original_image, (self._max_x, self._min_y), (self._max_x, self._max_y), (0,255,0), 3)
        
        # bottom line
        cv2.line(self._original_image, (self._min_x, self._max_y), (self._max_x, self._max_y), (0,255,0), 3)

        
    def getLength(self):
        '''
        Using the method of getting the max distance across and a nearly orthogonal vector of max distance to that one
        Hard to explain in words
        '''
        # we want to loop through the points contained in p for each contour. 
        # p is a set of points that form the contour so the contours contains a set of p per contour drawn
        # compute distance
        D = pdist(self.points)
        # input into an array
        D = squareform(D)
        # find max distance and which points this corresponds to
        self.pixellength = round(nanmax(D), 2)
        # called I_row and I_col since it is grabbing the "ij" location in a matrix where the max occurred.
        # the row number where it occurs represents one of the indices in the original self.points array where one of the points on the contour lies
        # the column number would be the point on the opposite side of the contour
        # L_row, and L_col since these indices correspond with coordinate points that give us the length
        [L_row, L_col] = unravel_index( argmax(D), D.shape )
        
        self.min_length_coord = tuple(self.points[L_row])
        self.max_length_coord = tuple(self.points[L_col])
        self.length_coords = [self.min_length_coord, self.max_length_coord]
        self.length_vector = np.array(self.max_length_coord) - np.array(self.min_length_coord)
        self.unit_length_vector = self.length_vector / norm(self.length_vector)
        self.length = round(self.pixellength * self.cm_pixel_ratio, 2) # px * mm / px yields units of mm
        return self.length
    def getWidth(self):
        # length axis represents a unit vector along the direction where we found the longest distance over the contour
        # length_axis = (np.array(p[L_col]) - np.array(p[L_row])) / norm(np.array(p[L_col]) - np.array(p[L_row]))
        '''above will be replaced with self.unit_length_vector'''
        # length_axis = self.unit_length_vector
       
        # all_vecs will be an list of vectors that are all the combinations of vectors that pass over the contour area
        all_vecs = []
        coordinates = []
        for i in range(0, len(self.points) - 1):
            for j in range(i + 1, len(self.points)):
                all_vecs.append(np.array(self.points[i]) - np.array(self.points[j]))
                coordinates.append([tuple(self.points[i]), tuple(self.points[j])])
        
        # make it a column of a pandas dataframe
        #vectors_df = DataFrame({'all_vecs': all_vecs, 'coordinates': coordinates})
        vectors_df = {'all_vecs': all_vecs, 'coordinates': coordinates}
        
        # Here we normalize all those vectors to prepare to take the dot product with the vector called "length vector"
        # Dot product will be used to determine orthogonality
        vectors_df['all_vecs_normalized'] = vectors_df.all_vecs.apply(lambda x: x / norm(x))

        # Take the dot product
        #vectors_df['dot_product'] = vectors_df.all_vecs_normalized.apply(lambda x: np.dot(x, length_axis))
        vectors_df['dot_product'] = vectors_df.all_vecs_normalized.apply(lambda x: abs(np.dot(x, self.unit_length_vector)))
        #vectors_df['orthogonal'] = vectors_df.dot_product.apply(lambda x: x < 0.15)
       
        vectors_df['norms'] = vectors_df.all_vecs.apply(lambda x: norm(x))

        if any(vectors_df.dot_product < 0.075):
            # allowing dot product to be up to 0.15 allows the length and width to have an angle of 81.37 to 90 degrees between each other
            width = nanmax(vectors_df[vectors_df.dot_product < 0.075].norms)
            self.width_coords = vectors_df[vectors_df.norms == width].sort_values('dot_product').coordinates.tolist()[0]
            self.pixelwidth = round(width, 2)
            self.width = round(self.pixelwidth * self.cm_pixel_ratio, 2) # pixels times cm / pixels yields units of millimeters
        else:
            self.pixelwidth = None
            self.width_coords = None
    
    def getArea(self, pixels = True):
        self.surfacearea_px2 = cv2.contourArea(self.points)
        self.surfacearea = cv2.contourArea(self.points) * (self.cm_pixel_ratio ** 2)
        return self.surfacearea_px2 if pixels == True else surfacearea

    def drawLength(self):
        "image represents the image we are drawing on"
        cv2.line(self._original_image, self.length_coords[0], self.length_coords[1], (0,255,0), 2)
        #cv2.putText(image, "L:%scm, W:%scm" % (self.length, self.width), self.length_coords[1], cv.FONT_HERSHEY_PLAIN, 1, (0,0,255), 2)
        #cv2.line(image, self.width_coords[0], self.width_coords[1], (0,255,0))
        return None
