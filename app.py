import os
import sqlite3
import click
import cs50

from flask import Flask, redirect, render_template, request, session, current_app, g, url_for
from flask_session import Session
from flask.cli import with_appcontext
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, outfitpicker, saveImage, dbInsert, dbSelect, addItemToCloset

# When running from terminal: export FLASK_ENV=development

# Configure application
app = Flask(__name__)

# Set configuration options
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
Session(app)

# @app.after_request
# def after_request(response):
#     """Ensure responses aren't cached"""
#     response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
#     response.headers["Expires"] = 0
#     response.headers["Pragma"] = "no-cache"
#     return response

# Routes
@app.route("/")
@login_required
def index():
    print('index')
    # Open database connection
    con = sqlite3.connect('outfits.db')
    print(con)
    con.row_factory = sqlite3.Row
    db = con.cursor()
    print(db)
    # Get categories
    db.execute('SELECT clothing.category, clothing.itemname FROM clothing JOIN closets ON clothing.id=closets.itemid WHERE closets.userid = ? GROUP BY category', (session['user_id'], ))
    info = db.fetchall()
    print(info)
    categories = []
    for i in range(len(info)):
        print(info[i]["category"])
        categories.append(info[i]["category"])

    # Get clothing
    items = []
    db.execute('SELECT * FROM clothing JOIN closets ON clothing.id=closets.itemid WHERE closets.userid = ?', (session['user_id'], ))
    items = db.fetchall()
    print(items)
    if items and len(items) > 3:
        outfit = outfitpicker(items)
        shoes = outfit[0]
        item1 = outfit[1]
        item2 = outfit[2]
        # if outfit[0]:
        #     return render_template('login.html')
        return render_template('index.html', categories=categories, shoes=shoes, item1=item1, item2=item2)
    else:
        # Had to redirect to closet if user had no items, like a new user
        # need a better way to handle this
        return redirect(url_for('mycloset'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        # Check required fields filled out
        if not request.form.get('username'):
            # TODO: pop-up saying must enter username
            return render_template('register.html')
        if not request.form.get('password'):
            # TODO: pop-up saying must enter password
            return render_template('register.html')
        if not request.form.get('confirmation'):
            # TODO: pop-up saying must re-enter password
            return render_template('register.html')
        if not request.form.get('password') == request.form.get('confirmation'):
            # TODO: pop-up saying passwords do not match
            return render_template('register.html')

        # Check username not taken
        con = sqlite3.connect('outfits.db')
        db = con.cursor()
        data = db.execute('SELECT * FROM users WHERE username = ?', (request.form.get('username'),))
        rows = data.fetchall()

        if not len(rows) == 0:
            # TODO: pop-up saying username taken
            return render_template('register.html')

        # Store new user in Database
        username = request.form.get('username')
        passwordHash = generate_password_hash(request.form.get('password'), method='scrypt:32768:8:1', salt_length=16)
        db.execute('INSERT INTO users (username, hash) VALUES (?, ?)', (username, passwordHash))
        con.commit()
        con.close()
        return render_template('index.html')
    else:
        return render_template('register.html')

@app.route('/login', methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # User reached route via POST
    if request.method == 'POST':
        if not request.form.get('username'):
            # TODO: pop-up saying must enter Username
            return render_template('login.html')
        if not request.form.get('password'):
            # TODO: pop-up saying must enter password
            return render_template('login.html')

        # Check username not taken
        con = sqlite3.connect('outfits.db')
        con.row_factory = sqlite3.Row
        db = con.cursor()
        #for row in db.execute('SELECT * FROM users WHERE username = ?', (request.form.get('username'),)):
            #id, user, hash = row
        data = db.execute('SELECT * FROM users WHERE username = ?', (request.form.get('username'),))
        rows = data.fetchall()
        id = rows[0][0]
        user = rows[0][1]
        hash = rows[0][2]
        print(id, user)
        # Ensure username exists and password is correct
        if user == None:
            print('user=none')
            return render_template('login.html')

        if user != request.form.get('username') or not check_password_hash(hash, request.form.get('password')):
            # TODO: pop-up saying username taken
            return render_template('register.html')
        # con.commit()
        con.close()
        # Remember which user has logged in
        session['user_id'] = id
        print(session)
        # Redirect to My Closet Page
        return redirect(url_for('index'))

    else:
        return render_template('login.html')

@app.route('/mycloset')
@login_required
def mycloset():
    # Get all top-level categories from closets database, submit to be listed as list options

    # Connect to DB
    con = sqlite3.connect('outfits.db')
    con.row_factory = sqlite3.Row
    db = con.cursor()

    # Get all categories
    db.execute('SELECT category FROM clothing GROUP BY category')
    temp1 = db.fetchall()
    allcategories = []
    for i in range(len(temp1)):
        allcategories.append(temp1[i]['category'])

    # Get user's categories
    db.execute('SELECT clothing.category, clothing.itemname FROM clothing JOIN closets ON clothing.id=closets.itemid WHERE closets.userid = ? GROUP BY category', (session['user_id'], ))
    info = db.fetchall()
    usercategories = []
    for i in range(len(info)):
        usercategories.append(info[i]["category"])

    # Get user's clothing items
    items = db.execute('SELECT * FROM clothing JOIN closets ON clothing.id=closets.itemid WHERE closets.userid = ?', (session['user_id'], ))
    items = items.fetchall()
    notowned = db.execute('select * from clothing where id NOT IN (select itemid from closets where userid = ?)', (session['user_id'], ))
    notowned = notowned.fetchall()

    return render_template('mycloset.html', usercategories=usercategories, items=items, notowned=notowned, allcategories=allcategories)

@app.route('/addtocloset', methods=['GET', 'POST'])
@login_required
def addtocloset():
    # Add existing clothing option to user's closet
    # How do I get which option user clicked on?
    if request.method == "POST":
        options = request.form.getlist('option')
        con = sqlite3.connect('outfits.db')
        db = con.cursor()
        for i in range(len(options)):
            db.execute('INSERT INTO closets VALUES (?,?)', (options[i], session['user_id']))
        con.commit()
        con.close()
        return redirect('/mycloset')
    else:
        return render_template('mycloset.html')

@app.route('/removefromcloset', methods=['POST'])
@login_required
def removefromcloset():
    # Remove item from user's closet
    item = request.form.get('item')
    con = sqlite3.connect('outfits.db')
    db = con.cursor()
    db.execute('DELETE FROM closets WHERE itemid = ? AND userid = ?', (item, session['user_id']))
    con.commit()
    con.close()
    return redirect('/mycloset')

@app.route('/logout')
def logout():

    # Forget any user_id
    session.clear()

    # Redirect to home
    return redirect('/')

@app.route('/additem', methods=['POST'])
def additem():
    if request.method != "POST":
        return redirect(url_for('mycloset'))
    
    print(request.form, request.files)
    path = None
    if 'clothingImage' in request.files:
        print('clothingImage')
        file = request.files['clothingImage']
        if file.filename == '':
            path = None
        else:
            path = saveImage(file)
        print(path)
    # Save new clothing item to clothing database
    query = 'INSERT INTO clothing (itemname, category, imagePath) VALUES (?, ?, ?)'
    values = (request.form.get('item'), request.form.get('category'), path,)
    print(values)
    rowId = dbInsert(query, values)
    print(rowId)
    # Add new item to user's closet
    addItemToCloset(rowId, session['user_id'])
    # Return user to their closet page
    return redirect(url_for('mycloset'))
