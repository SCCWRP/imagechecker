from flask import render_template, request, jsonify, current_app, Blueprint, session
from werkzeug.utils import secure_filename
from glob import glob
import os, time, json, pika
import pandas as pd

# custom imports, from local files
from .utils.html import htmltable

homepage = Blueprint('homepage', __name__)
@homepage.route('/')
def index():
    session.clear()
    session['submissionid'] = int(time.time())
    session['submission_dir'] = os.path.join(os.getcwd(), "files", str(session['submissionid']))
    os.mkdir(session['submission_dir'])
    os.mkdir(os.path.join(session['submission_dir'], "crops"))
    os.mkdir(os.path.join(session['submission_dir'], "data"))

    return render_template('index.html')



@homepage.route('/login', methods = ['GET','POST'])
def login():

    login_info = dict(request.form)
    print(login_info)
    session['login_info'] = login_info

    return jsonify(msg="login successful")


    
@homepage.route('/upload',methods = ['GET','POST'])
def upload():
    
    # -------------------------------------------------------------------------- #

    # First, the routine to upload the file(s)

    # routine to grab the uploaded file
    print("uploading files")
    files = request.files.getlist('files[]')
    if len(files) == 1:
    
        for f in files:
            # i'd like to figure a way we can do it without writing the thing to an excel file
            f = files[0]
            filename = secure_filename(f.filename)
            session['originalphoto'] = filename

            # if file extension is xlsx/xls (hopefully xlsx)
            img_path = os.path.join( session['submission_dir'], str(filename) )

            # the user's uploaded excel file can now be read into pandas
            f.save(img_path)


    elif len(files) > 1:
        return jsonify(user_error_msg="Too many files given, as of now it can only handle one")
    else:
        return jsonify(user_error_msg="No file given")

    print("DONE uploading files")



    # -------------------------------------------------------------------------- #

    # Identify objects

    # Here in an excel submission we figure out what datatype they are submitting for
    # In this stage we can identify which objects are in the image


    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq')
    )
    channel = connection.channel()

    channel.queue_declare(queue='obj_detect')

    # ----- Send message and listen for response from rabbit mq ----- #

    f = open(os.path.join(session.get("submission_dir"), "status.json"), 'w')
    try:
        f.write(json.dumps({
            "status":"sent"
        }))
        msgbody = json.dumps({
            "submission_dir": session.get("submission_dir"),
            "originalphoto": session.get("originalphoto")
        })
        channel.basic_publish(
            exchange = '', 
            routing_key = 'obj_detect', 
            body = msgbody
        )
        print(f"Sent {msgbody}")
        connection.close()
    except Exception as e:
        print(e)
        print("Something went wrong sending the data to rabbitmq")
        raise Exception(e)
    f.close()

    import time

    # 300 seconds = 5 minutes
    timeout = time.time() + 300

    while time.time() < timeout:
        time.sleep(1) # dont want to use excessive CPU recources
        f = open(os.path.join(session.get("submission_dir"), "status.json"), 'r')
        response = json.loads(f.read())
        f.close()
        assert response.get("status") in ("sent","done","error"), \
            f"Invalid status message {response.get('status')} in the status file"
        if response.get('status') == "done":
            break
        elif response.get("status") == "error":
            raise Exception(response.get("errmsg"))
    session['markedphotopath'] = response.get('markedphoto')
    session['markedphoto'] = \
        response.get('markedphoto').rsplit('/', 1)[-1] \
        if response.get('markedphoto') is not None else ''




    # ----------------------------------------- #


    # data = pd.DataFrame({
    #     "objectid"        : [i for i in range(max_cropnumber)],
    #     "submissionid"      : [session['submissionid'] for i in range(max_cropnumber)],
    #     "originalphotoname" : [session['originalphoto'] for i in range(max_cropnumber)],
    #     "cropnumber"        : [i + 1 for i in range(max_cropnumber)]
    # })
    data = pd.DataFrame({
        "objectid"   : [i for i in response.get("boundingboxes").keys()],
        "cropnumber" : [i for i in response.get("boundingboxes").keys()],
        "minx"       : [response.get("boundingboxes").get(i)[0] for i in response.get("boundingboxes").keys()],
        "miny"       : [response.get("boundingboxes").get(i)[1] for i in response.get("boundingboxes").keys()],
        "maxx"       : [response.get("boundingboxes").get(i)[2] for i in response.get("boundingboxes").keys()],
        "maxy"       : [response.get("boundingboxes").get(i)[3] for i in response.get("boundingboxes").keys()],
    }) \
    .assign(
        submissionid = session.get('submissionid'),
        originalphoto = session.get('originalphoto'),
        **session.get('login_info')
    )

    data.to_excel( os.path.join(session['submission_dir'], "data", "data.xlsx") )
    
    htmlfile = open( os.path.join(session['submission_dir'], "data", "data.html" ) , 'w')
    htmlfile.write(htmltable(data))
    htmlfile.close()


    print("DONE with upload routine, returning JSON to browser")
    json_response = {
        "submissionid": session['submissionid'], 
        "originalphoto": session['originalphoto'],
        "markedphoto" : session.get("markedphoto")
    }
    print(json_response)
    return jsonify(**json_response)

