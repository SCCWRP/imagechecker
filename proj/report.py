from flask import Blueprint, request, session, render_template
import os

report = Blueprint('report', __name__)
@report.route('/report',methods = ['GET','POST'])
def getreport():
    htmlfile = open( os.path.join(session['submission_dir'], "data", "data.html" ) , 'r')
    data = htmlfile.read()
    htmlfile.close()

    if session['n_crops'] > 0:
        return render_template(
            "imgreport.html",
            submissionid = session['submissionid'], 
            originalphoto = session['originalphoto'], 
            cropnumbers = [i + 1 for i in range(session['n_crops'])],
            data = data
        )
    else:
        return "No possible codes found" 
