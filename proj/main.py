from flask import render_template, request, jsonify, current_app, Blueprint, session
from werkzeug.utils import secure_filename
from glob import glob
from inspect import currentframe
import os, time, json, pika
import pandas as pd

# custom imports, from local files
from .utils.html import htmltable
from .utils.mail import send_mail

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
    assert 'login_email' in login_info.keys(), "There is no login_email field in the login form"
    session['login_info'] = login_info
    return jsonify(msg="logged in successfully")

    
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
            print("Error in the routine of processing the image - from the RabbitMQ consumer")
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
        "min_y"       : [round(response.get("boundingboxes").get(i)[0], 4) for i in response.get("boundingboxes").keys()],
        "min_x"       : [round(response.get("boundingboxes").get(i)[1], 4) for i in response.get("boundingboxes").keys()],
        "max_y"       : [round(response.get("boundingboxes").get(i)[2], 4) for i in response.get("boundingboxes").keys()],
        "max_x"       : [round(response.get("boundingboxes").get(i)[3], 4) for i in response.get("boundingboxes").keys()]
    }) \
    .assign(
        speciesid = "",
        submissionid = session.get('submissionid'),
        originalphoto = session.get('originalphoto'),
        **session.get('login_info')
    )

    data.to_excel( os.path.join(session['submission_dir'], "data", "data.xlsx") )
    
    htmlfile = open( os.path.join(session['submission_dir'], "data", "data.html" ) , 'w')
    htmlfile.write(htmltable(data, cssclass="table", editable_fields=('length','width','area','speciesid')))
    htmlfile.close()


    print("DONE with upload routine, returning JSON to browser")
    json_response = {
        "submissionid" :  session['submissionid'], 
        "originalphoto":  session['originalphoto'],
        "markedphoto"  :  session.get("markedphoto")
    }
    print(json_response)
    return jsonify(**json_response)


# When an exception happens when the browser is sending requests to the homepage blueprint, this routine runs
@homepage.errorhandler(Exception)
def homepage_error_handler(error):
    print(f"Exception occurred in {currentframe().f_code.co_name}")
    print(str(error))
    response = {
        "message": "Internal Server Error",
        "error"  : str(error)
    }
    msgbody = "Image checker crashed\n\n"
    msgbody += f"Error message: {error}\n\n"
    msgbody += f"Login Information:\n\t"
    for k, v in session.get('login_info').items():
            msgbody += f"{k}: {v}\n\t"
    send_mail(
        current_app.send_from,
        current_app.maintainers,
        "Image Checker Internal Server Error", 
        msgbody,
        server = current_app.config['MAIL_SERVER']
    )
    return jsonify(**response)