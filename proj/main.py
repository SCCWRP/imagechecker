from flask import render_template, request, jsonify, current_app, Blueprint, session
from werkzeug.utils import secure_filename
from glob import glob
import os, time, json, cv2
import pandas as pd

# custom imports, from local files
from .imgutils.functions import crop_qr
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

    # Here instead we will attempt to extract the QR codes from the image
    for im in ( glob(os.path.join(session['submission_dir'], "*.jpg")) + glob(os.path.join(session['submission_dir'], "*.png"))):
        max_cropnumber = crop_qr(im, os.path.join(session['submission_dir'], "crops") )
    
    session['n_crops'] = max_cropnumber

    # ----------------------------------------- #


    data = pd.DataFrame({
        "objectid"        : [i for i in range(max_cropnumber)],
        "submissionid"      : [session['submissionid'] for i in range(max_cropnumber)],
        "originalphotoname" : [session['originalphoto'] for i in range(max_cropnumber)],
        "cropnumber"        : [i + 1 for i in range(max_cropnumber)]
    })
    data.to_excel( os.path.join(session['submission_dir'], "data", "data.xlsx") )
    
    htmlfile = open( os.path.join(session['submission_dir'], "data", "data.html" ) , 'w')
    htmlfile.write(htmltable(data))
    htmlfile.close()


    print("DONE with upload routine, returning JSON to browser")
    json_response = {
        "submissionid": session['submissionid'], 
        "originalphoto": session['originalphoto'],
        "n_crops": max_cropnumber
    }
    print(json_response)
    return jsonify(**json_response)

