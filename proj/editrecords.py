from flask import render_template, request, jsonify, current_app, Blueprint, session
from werkzeug.utils import secure_filename
from glob import glob
from inspect import currentframe
import os, time, json, pika
import pandas as pd

# custom imports, from local files
from .utils.html import htmltable
from .utils.mail import send_mail

editor = Blueprint('editor', __name__)
@editor.route('/edit-submission/<submissionid>', methods = ['GET','POST'])
def display_records(submissionid):
    if submissionid:
        session['submissionid'] = str(submissionid)
        rawdata = pd.read_sql(f"SELECT * FROM tbl_testfish WHERE submissionid = {submissionid}", current_app.eng)
        data = htmltable(rawdata, cssclass="table", editable_fields=('length','lengthunits','width','area','speciesid'))

        markedphotos = [
            ''.join([str(x).rsplit('.', 1)[0], '-marked.',str(x).rsplit('.', 1)[-1]]) for x in rawdata.originalphoto.unique()
        ]
        return render_template('editrecords.html', data=data, submissionid=submissionid, markedphotos=markedphotos)
    else:
        return jsonify(message="No submissionid provided")


@editor.route('/savechanges', methods = ['GET','POST'])
def savechanges():
    
    data = pd.DataFrame(request.get_json())

    submissionid = str(session.get('submissionid'))
    assert submissionid, "No submissionid provided (in savechanges routine)" 
    
    data.to_excel(os.path.join(os.getcwd(), "files", submissionid, "data", "data.xlsx"))

    htmlfile = open( os.path.join(os.getcwd(), "files", submissionid, "data", "data.html" ) , 'w')
    htmlfile.write(htmltable(data, cssclass="table", editable_fields=('length','lengthunits','width','area','speciesid')))
    htmlfile.close()
    
    return jsonify(message="data saved successfully")




# When an exception happens when the browser is sending requests to the editor blueprint, this routine runs
@editor.errorhandler(Exception)
def editor_error_handler(error):
    print(f"Exception occurred in {currentframe().f_code.co_name}")
    print(str(error))
    response = {
        "message": "Internal Server Error",
        "error"  : str(error)
    }
    msgbody = "Image checker crashed\n\n"
    msgbody += f"Error message: {error}\n\n"
    if session.get('login_info'):
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