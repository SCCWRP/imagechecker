#!/usr/bin/python3
import numpy as np
import tensorflow as tf
from PIL import Image
import time, pika, json, cv2, os
import matplotlib.pyplot as plt

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



def listen():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='obj_detector')

    MODEL_PATH = '/var/www/imagechecker/proj/imgutils/fish_inception_v2_graph/frozen_inference_graph.pb'
    object_detector = Object_Detector(MODEL_PATH)

    # The callback function will be the full reformatting routine
    def callback(ch, method, properties, body):
        try:
            print(" [x] Received %r" % body)
            data = json.loads(body)
            # Make the green box around the image

            img = cv2.imread(os.path.join(data.get("submission_dir"), data.get("originalphoto")))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_, boxes = object_detector.detect_image(img, score_thr=0.2)

            print("boxes")
            print(boxes)

            markedphotopath = os.path. \
            join(
                data.get("submission_dir"), 
                "{}-marked.jpg".format(data.get('originalphoto').rsplit('.',1)[0])
            )

            cv2.imwrite(markedphotopath, img_)

            f = open(os.path.join(data.get("submission_dir"), "status.json"), 'w')
            f.write(
                json.dumps({
                    "status": "done",
                    "boundingboxes": boxes,
                    "markedphoto": markedphotopath
                })
            )
            f.close()
        except Exception as e:
            print("Exception:")
            print(e)
            f = open(os.path.join(data.get("submission_dir"), "status.json"), 'w')
            f.write(
                json.dumps({
                    "status": "error",
                    "errmsg": str(e)
                })
            )
            f.close()



    channel.basic_consume(queue='obj_detect', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    listen()