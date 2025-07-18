import os
import urllib.parse
from random import randrange

from flask import redirect, render_template, request, session, url_for
from functools import wraps
from werkzeug.utils import secure_filename
from utils.db import dbInsert, dbSelect

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def pickOutfit(items, top=None, bottom=None, shoes=None):

    while not (shoes and top and bottom):
        rand = randrange(len(items))
        if items[rand]['category'] == 'Shoes' and not shoes:
            shoes = items[rand]
            continue
        if items[rand]['category'] == 'Top' and not top:
            top = items[rand]
            continue
        if items[rand]['category'] == 'Bottom' and not bottom:
            bottom = items[rand]
            continue
        if items[rand]['category'] == 'Dress' and not top and not bottom:
            top = items[rand]
            bottom = top
            continue

    outfit = {
        'shoes': shoes,
        'top': top,
        'bottom': bottom
    }
    print(outfit)
    
    return outfit

# def saveImage(file):
#     # safely save image in file system
#     filename = secure_filename(file.filename)
#     file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
#     # return full filepath to save in database
#     return os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

# def processImageSubmission(requestFiles):
#     # Receives request.files and checks for clothingImage, saving an uploaded image and returning the filepath
#     path = None
#     if 'clothingImage' in requestFiles:
#         file = requestFiles['clothingImage']
#         if file.filename == '':
#             path = None
#         else:
#             path = saveImage(file)
    
#     return path

# def getDbConnection(withRow=True):
#     # Open database connection and return cursor, option to return indexed and named access to columns
#     con = sqlite3.connect('outfits.db')
#     if withRow:
#         con.row_factory = sqlite3.Row

#     return con

# def dbInsert(query, values):
#     db = getDbConnection(False)
#     cur = db.cursor()
#     cur.execute(query, values)
#     rowId = cur.lastrowid
#     db.commit()
#     db.close()

#     return rowId

# def dbSelect(query, values=None):
#     db = getDbConnection(True)
#     cur = db.cursor()
#     if values:
#         data = cur.execute(query, values).fetchall()
#     else:
#         data = cur.execute(query).fetchall()
#     db.close()
#     return data


def createItem(itemName, category, imagePath, userId, needsPair=1, material=''):
    query = 'INSERT INTO clothing (itemname, category, needsPair, imagePath, userId, material) VALUES (?, ?, ?, ?, ?, ?)'
    values = (itemName, category, needsPair, imagePath, userId, material,)
    id = dbInsert(query, values)

    return id

def updateItem(itemId, itemName, category, material=''):
    query = 'UPDATE clothing SET itemname = ?, category = ?, material = ? WHERE id = ?'
    values = (itemName, category, material, itemId,)
    dbInsert(query, values)

    return True

def updateItemImage(itemId, imagePath):
    query = 'UPDATE clothing SET imagePath = ? where id = ?'
    values = (imagePath, itemId,)
    dbInsert(query, values)

    return True

def processItemUpdate(itemDetails, imagePath):
    # Need to only update fields that the user submitted new data for
    if imagePath:
        updateItemImage(itemDetails['id'], imagePath)
    
    updateItem(itemDetails['id'], itemDetails['itemName'], itemDetails['category'], itemDetails['material'])

    return True
