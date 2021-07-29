from flask import Blueprint, current_app, session, jsonify
from .utils.db import GeoDBDataFrame
from inspect import currentframe

import pandas as pd
import json, os

from .utils.mail import send_mail

finalsubmit = Blueprint('finalsubmit', __name__)
@finalsubmit.route('/load', methods = ['GET','POST'])
def load():
    # try:
        eng = current_app.eng

        data = pd.read_excel( os.path.join(session['submission_dir'], "data", "data.xlsx") )

        data = data.assign(
            objectid = "sde.next_rowid('sde','tbl_testfish')",
            globalid = "sde.next_globalid()"
        )

        data = GeoDBDataFrame(data)

        data.to_geodb("tbl_testfish", eng)

        msgbody = "Successful Image Data Submission\n\n"
        msgbody += f"SubmissionID: {session.get('submissionid')}\n\n"
        msgbody += f"Login Information:\n\t"
        for k, v in session.get('login_info').items():
                msgbody += f"{k}: {v}\n\t"
        send_mail(
            current_app.send_from,
            [*current_app.maintainers, session.get('login_info').get('login_email')],
            f"Successful Image Data Submission - ID#{session.get('submissionid')}", 
            msgbody,
            server = current_app.config['MAIL_SERVER']
        )

        return jsonify(user_notification="Sucessfully loaded data")
    # except Exception as e:
    #     print(e)
    #     return jsonify(user_notification="Error loading data")
        
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