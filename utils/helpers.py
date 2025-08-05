import os
import urllib.parse
from random import randrange

from flask import redirect, render_template, request, session, url_for
from functools import wraps
from werkzeug.utils import secure_filename
from utils.db import dbInsert, dbSelect, getItemImagePath, dbDelete
from utils.images import deleteImage

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
        if items[rand]['needsPair'] == 0 and not top and not bottom:
            top = items[rand]
            bottom = top
            continue
        if items[rand]['category'] == 'Shoes' and not shoes:
            shoes = items[rand]
            continue
        if items[rand]['category'] == 'Top' and not top:
            top = items[rand]
            continue
        if items[rand]['category'] == 'Bottom' and not bottom:
            bottom = items[rand]
            continue

    outfit = {
        'shoes': shoes,
        'top': top,
        'bottom': bottom
    }
    
    return outfit

def getItem(itemId):
    item = dbSelect('SELECT * FROM clothing WHERE id = ?', (itemId,))[0]
    return item

def processIndexRequestData(data):
    processed = {
        'Top': None,
        'Bottom': None,
        'Shoes': None
    }
    if 'Top' in data:
        processed['Top'] = getItem(data['Top'])
    if 'Bottom' in data:
        processed['Bottom'] = getItem(data['Bottom'])
    if 'Shoes' in data:
        processed['Shoes'] = getItem(data['Shoes'])
    for key in data.keys():
        if key not in processed.keys():
            item = getItem(data[key])
            if item['needsPair'] == 0:
                processed['Top'] = item
                processed['Bottom'] = processed['Top']

    return processed
    

def createItem(itemName, category, imagePath, userId, needsPair=1, material=''):
    query = 'INSERT INTO clothing (itemname, category, needsPair, imagePath, userId, material) VALUES (?, ?, ?, ?, ?, ?)'
    values = (itemName, category, needsPair, imagePath, userId, material,)
    id = dbInsert(query, values)

    return id

def updateItem(itemId, itemName, category, needsPair=1, material=''):
    query = 'UPDATE clothing SET itemname = ?, category = ?, material = ?, needsPair = ? WHERE id = ?'
    values = (itemName, category, material, needsPair, itemId,)
    dbInsert(query, values)

    return True

def updateItemImage(itemId, imagePath):
    query = 'UPDATE clothing SET imagePath = ? where id = ?'
    values = (imagePath, itemId,)
    dbInsert(query, values)

    return True

def deleteItemImage(itemId):
    path = getItemImagePath(itemId)
    deleted = deleteImage(path)
    return deleted

def processItemUpdate(itemDetails, imagePath):
    # Need to only update fields that the user submitted new data for
    if imagePath:
        deleteItemImage(itemDetails['id'])
        updateItemImage(itemDetails['id'], imagePath)
    
    updateItem(itemDetails['id'], itemDetails['itemName'], itemDetails['category'], itemDetails['needsPair'], itemDetails['material'])

    return True

def processItemDeletion(itemId):
    # Delete item's image
    deleteItemImage(itemId)
    # Delete item from db
    rowCount = dbDelete('DELETE FROM clothing WHERE id = ?', (itemId,))
    # Confirm item no longer exists in db
    return rowCount == 1
    