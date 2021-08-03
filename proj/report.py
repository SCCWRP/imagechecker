from flask import Blueprint, request, session, render_template
import os

report = Blueprint('report', __name__)
@report.route('/report',methods = ['GET','POST'])
def getreport():
    try:
        htmlfile = open( os.path.join(session['submission_dir'], "data", "data.html" ) , 'r')
        data = htmlfile.read()
        htmlfile.close()
    except FileNotFoundError:
        data = ""

    if session.get('markedphoto'):
        return render_template(
            "imgreport.html",
            submissionid = session.get('submissionid'), 
            originalphoto = session.get('originalphoto'), 
            markedphoto = session.get('markedphoto'),
            data = data
        )
    else:
        return "Unable to obtain data from image" 
