from flask import Blueprint, send_file, send_from_directory, request
import os

media = Blueprint('media', __name__)
@media.route('/media',methods = ['GET','POST'])
def getfile():
    submissionid = str(request.args.get("submissionid"))
    cropnumber = request.args.get("crop")
    original_photoname = request.args.get("originalphoto")

    print(submissionid)
    print(cropnumber)
    print(original_photoname)

    if submissionid is None:
        return "No submission id provided"
    if original_photoname is None:
        return "No photoname provided"

    if cropnumber:
        print(os.path.join(os.getcwd(), "files", submissionid, "crops", f"crop{cropnumber}___{original_photoname}"))
        return send_file(os.path.join(os.getcwd(), "files", submissionid, "crops", f"crop{cropnumber}___{original_photoname}"), f"crop{cropnumber}-{original_photoname}")
    return "i dont know what happened"
send_from_directory