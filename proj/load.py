from flask import Blueprint, current_app, session, jsonify
from .utils.db import GeoDBDataFrame

import pandas as pd
import json, os

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

        return jsonify(user_notification="Sucessfully loaded data")
    # except Exception as e:
    #     print(e)
    #     return jsonify(user_notification="Error loading data")
        
