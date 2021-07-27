from flask import Blueprint, send_file, send_from_directory, request
import os

media = Blueprint('media', __name__)
@media.route('/media',methods = ['GET','POST'])
def getfile():
    submissionid = str(request.args.get("submissionid"))
    photoname = request.args.get("photo")

    print(submissionid)
    print(photoname)

    if submissionid is None:
        return "No submission id provided"
    if photoname is None:
        return "No photoname provided"

    
    print(os.path.join(os.getcwd(), "files", submissionid, photoname))
    #return send_file(os.path.join(os.getcwd(), "files", submissionid, "crops", f"crop{cropnumber}___{photoname}"), f"crop{cropnumber}-{photoname}")
    return send_file(os.path.join(os.getcwd(), "files", submissionid, photoname))
