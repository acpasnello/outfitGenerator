import os
import urllib.parse
from random import randrange

from flask import redirect, render_template, request, session, url_for
from functools import wraps
from werkzeug.utils import secure_filename

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def outfitpicker(items):
    # Does pickrand need to be submitted? No
    # Initialize outfit variables, should they be empty lists, dicts, or None/Null?
    shoes = {}
    item1 = {}
    item2 = {}
    # outfit = [shoes, item1, item2]
    # outfit = [3]
    # outfit[0] = shoes
    # outfit[1] = item1
    # outfit[2] = item2
    pickrand = randrange(len(items))

    # Generate Outfit
    while not (shoes and item1 and item2):
        pickrand = randrange(len(items))
        if not shoes:
            if items[pickrand]['category'] == 'Shoes':
                shoes = items[pickrand]
                # restart loop
                continue
        if not item1:
            if items[pickrand]['category'] == 'Shoes':
                continue
            # if needspair is true
            if items[pickrand]['needspair'] == 1:
                item1 = items[pickrand]
                continue
            elif items[pickrand]['needspair'] == 0:
                # if needspair is false
                item1 = items[pickrand]
                item2 = item1
            # restart loop
            continue
        if not item2:
            if item1['category']==items[pickrand]['category']:
                continue
            elif items[pickrand]['needspair'] == 0:
                continue
            elif items[pickrand]['category'] == 'Shoes':
                continue
            else:
                item2 = items[pickrand]

    # Reorder for display purposes
    if item1['category'] == 'Bottom':
        temp = item1
        item1 = item2
        item2 = temp
    elif item2['category'] == 'Top':
        temp = item2
        item2 = item1
        item1 = temp
    outfit = [shoes, item1, item2]

    return outfit

def saveImage(file):
    # safely save image in file system
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    # return full filepath to save in database
    return os.path.join(app.config['UPLOAD_FOLDER'], filename)
