from flask import Blueprint, current_app, session, jsonify, request
from .utils.db import GeoDBDataFrame
from inspect import currentframe

import pandas as pd
import json, os

from .utils.mail import send_mail

finalsubmit = Blueprint('finalsubmit', __name__)
@finalsubmit.route('/load', methods = ['GET','POST'])
def load():
    eng = current_app.eng
    table = 'tbl_testfish'

    submissionid = str(session.get('submissionid'))
    assert submissionid, "SubmissionID not provided"

    assert os.path.exists(os.path.join(os.getcwd(), "files", submissionid, "data", "data.xlsx")), f"Data not found for submissionid {submissionid}"

    data = pd.read_excel( os.path.join(os.getcwd(), "files", submissionid, "data", "data.xlsx") )

    data = data.assign(
        objectid = f"sde.next_rowid('sde','{table}')",
        globalid = "sde.next_globalid()"
    )

    data = GeoDBDataFrame(data)

    data.to_geodb(table, eng)

    msgbody = "Successful Image Data Submission\n\n"
    msgbody += f"SubmissionID: {submissionid}\n\n"
    msgbody += f"Login Information:\n\t"
    for k, v in session.get('login_info').items():
            msgbody += f"{k}: {v}\n\t"
    send_mail(
        current_app.send_from,
        [*current_app.maintainers, session.get('login_info').get('login_email')],
        f"Successful Image Data Submission - ID#{submissionid}", 
        msgbody,
        server = current_app.config['MAIL_SERVER']
    )

    return jsonify(user_notification="Sucessfully loaded data")

        
# When an exception happens when the browser is sending requests to the finalsubmit blueprint, this routine runs
@finalsubmit.errorhandler(Exception)
def finalsubmit_error_handler(error):
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