#!/usr/bin/python3
import numpy as np
import pandas as pd
from PIL import Image
import time, pika, json, cv2, os, shutil
import matplotlib.pyplot as plt

from utils.html import htmltable
from contours import Contour, Object_Detector

def listen():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='obj_detector')


    # The callback function will be the full reformatting routine
    def callback(ch, method, properties, body):
        try:
            print(" [x] Received %r" % body)
            data = json.loads(body)
            # Make the green box around the image

            FISH_DETECTOR = Object_Detector('/var/www/imagechecker/proj/imgutils/fish_inception_v2_graph/frozen_inference_graph.pb')

            originalphotopath = os.path.join(data.get('submission_dir'), data.get('originalphoto'))
            
            markedphotopath = os.path. \
            join(
                data.get("submission_dir"), 
                "{}-marked.{}" \
                .format(
                    data.get('originalphoto').rsplit('.',1)[0],
                    data.get('originalphoto').rsplit('.',1)[-1]
                )
            )

            shutil.copy(originalphotopath, markedphotopath)
            
            img = cv2.imread(markedphotopath)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            ret, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

            # Grab contours
            contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            # filter down to ones between 200 and 2000 points, making the assumption that all else is pure noise
            contours = [c for c in contours if (200 < len(c) < 2000)]

            # Mark contours of interest on the image
            cv2.drawContours(img, contours, -1, (0,255,0), 1)

            # Now the contours will become our customized Contour object
            contours = [
                Contour(
                    points = c.reshape(c.shape[0],c.shape[-1]), 
                    original_image = img, 
                    output_photo_path = markedphotopath,
                    detector = FISH_DETECTOR
                ) 
                for c in contours
            ]

            # Should be self explanatory
            circles = [c for c in contours if c.isCircle()]
            fish = [c for c in contours if (c.containsFish() and (not c.isCircle()) )]

            # initialize the dataframe that we will append to
            output_df = pd.DataFrame({"objectid" : [], "cropnumber" : [], "min_y" : [], "min_x" : [], "max_y" : [], "max_x" : [], "length": [], "lengthunits": []}) 

            # We are making an assumption that the circle contour is a quarter
            if len(circles) != 1:
                print("unable to measure")
                cm_pixel_ratio = 1 # default placeholder. Not even sure if this should be here
                lengthunits = "px"
            else: 
                cm_pixel_ratio = 2.426 / circles[0].getLength() # We assume the circle contour is a quarter, which is 2.426cm in diameter
                lengthunits = "cm"

            # fc = fish contour
            for i, fc in enumerate(fish):
                fc.markBoundingBox()
                fc.drawLength()
                cv2.putText(
                    img, 
                    "fish {}".format(int(i)), 
                    fc.length_coords[1], 
                    cv2.FONT_HERSHEY_PLAIN, 
                    1, 
                    (0,0,255), 
                    2
                )
                output_df = pd.concat(
                    [
                        output_df,
                        pd.DataFrame({
                            "objectid": [int(i)],
                            "cropnumber": [int(i)],
                            "min_x": [fc._min_x],
                            "min_y": [fc._min_y],
                            "max_x": [fc._max_x], 
                            "max_y": [fc._max_y],
                            "length": [round(fc.getLength() * cm_pixel_ratio, 2)],
                            "lengthunits": lengthunits
                        })
                    ],
                    ignore_index = True
                )


            # save marked photo
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            cv2.imwrite(markedphotopath, img)

            f = open(os.path.join(data.get("submission_dir"), "status.json"), 'w')
            f.write(
                json.dumps({
                    "status": "done",
                    "markedphotopath": markedphotopath,
                    "data": output_df.to_dict()
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