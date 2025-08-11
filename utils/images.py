import os
from flask import current_app
from werkzeug.utils import secure_filename
# from PIL import Image

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'avif'}

def saveImage(file):
    # safely save image in file system
    filename = secure_filename(file.filename)
    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    # return full filepath to save in database
    return os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

def processImageSubmission(requestFiles):
    # Receives request.files and checks for clothingImage, saving an uploaded image and returning the filepath
    path = None
    if 'clothingImage' in requestFiles:
        file = requestFiles['clothingImage']
        if file.filename == '':
            path = None
        if file and checkTypeAllowed(file.filename):
            path = saveImage(file)
                
    return path

def checkImageType(filename):
    allowedTypes = {'png', 'jpg', 'jpeg', 'webp', 'avif'}
    f,e = os.path.splitext(filename)
    print(e)
    if e[1:].lower() in allowedTypes:
        print("allowed type")
        return True
    else:
        print('not allowed type')
        return False
    
# def convertTifftoJpg(imagePath):
#     f, e = os.path.splitext(imagePath)
#     outfile = f + '.jpg'
#     if imagePath != outfile:
#         try:
#             with Image.open(imagePath) as im:
#                 im.save(outfile)
#         except OSError:
#             print("cannot convert", imagePath)

def checkTypeAllowed(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def deleteImage(path):
    if os.path.exists(path):
        os.remove(path)
        return True
    else:
        return False
    