import os
import sqlite3
import click
import cs50

from flask import Flask, redirect, render_template, request, session, current_app, g
from flask_session import Session
from flask.cli import with_appcontext
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Set configuration options
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Routes
@app.route("/")
def index():
    return render_template('index.html')

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
        passwordHash = generate_password_hash(request.form.get('password'), method='sha1', salt_length=8)
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
        db = con.cursor()
        for row in db.execute('SELECT * FROM users WHERE username = ?', (request.form.get('username'),)):
            id, user, hash = row

        # Ensure username exists and password is correct
        if user == None:
            return render_template('login.html')

        if user != request.form.get('username') or not check_password_hash(hash, request.form.get('password')):
            # TODO: pop-up saying username taken
            return render_template('login.html')
        con.commit()
        con.close()
        # Remember which user has logged in
        session['user_id'] = id
        # Redirect to My Closet Page
        return redirect('/')

    else:
        return render_template('login.html')

@app.route('/mycloset')
def mycloset():
    # Needs loginrequired decoration
    # Get all top-level categories from closets database, submit to be listed as list options
    # Get all items for each category, submit to be listed under each category
    con = sqlite3.connect('outfits.db')
    con.row_factory = sqlite3.Row
    db = con.cursor()
    # Join clothing and closets on clothingID to only select categories where clothing.userID = session["user_id"], HAVING clothingID?
    db.execute('SELECT clothing.category, clothing.itemname FROM clothing JOIN closets ON clothing.id=closets.itemid WHERE closets.userid = ? GROUP BY category', (session['user_id'], ))
    # db.execute('SELECT category FROM clothing GROUP BY category') # returning list of tuples
    info = db.fetchall()
    categories = []
    for i in range(len(info)):
        categories.append(info[i]["category"])
    items = db.execute('SELECT * FROM clothing JOIN closets ON clothing.id=closets.itemid WHERE closets.userid = ?', (session['user_id'], ))
    items = items.fetchall()
    notowned = db.execute('select * from clothing where id NOT IN (select itemid from closets where userid = ?)', (session['user_id'], ))
        # clothingID NOT IN (select * from closet WHERE userid = session["user_id"])
    notowned = notowned.fetchall()
    return render_template('mycloset.html', categories=categories, items=items, notowned=notowned)

@app.route('/myclosetlist')
def myclosetlist():

    return render_template('myclosetlist.html')

@app.route('/logout')
def logout():

    # Forget any user_id
    session.clear()

    # Redirect to home
    return redirect('/')
