import os
import sqlite3

from flask import Flask, redirect, render_template, request, session, current_app, g, url_for
from flask_session import Session
from flask.cli import with_appcontext
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

from utils.helpers import login_required, pickOutfit, dbSelect, createItem, processItemUpdate, processIndexRequestData, processItemDeletion, processRegistration
from utils.images import processImageSubmission

# Configure application
app = Flask(__name__)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

# Set configuration options
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
Session(app)

# Routes
@app.route("/")
@login_required
def index():
     # Get clothing
    items = dbSelect('SELECT * FROM clothing WHERE userid = ?', (session['user_id'],))

    if request.args:
        data = request.args
        processedData = processIndexRequestData(data)
        outfit = pickOutfit(items, processedData['Top'], processedData['Bottom'], processedData['Shoes'])
    else:
        if items and len(items) >= 3:
            outfit = pickOutfit(items)
        else:
            # Had to redirect to closet if user had too few items
            return redirect(url_for('mycloset'))
    return render_template('index.html', item1=outfit['top'], item2=outfit['bottom'], shoes=outfit['shoes'])

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Check required fields filled out
        if not request.form.get('username'):
            messages = [{
                'text': 'Please enter a username.',
                'class': 'danger'
            }]
            return render_template('register.html', messages=messages)
        if not request.form.get('password'):
            messages = [{
                'text': 'Password required.',
                'class': 'danger'
            }]
            return render_template('register.html', messages=messages)
        if not request.form.get('confirmation'):
            messages = [{
                'text': 'Password confirmation required.',
                'class': 'danger'
            }]
            return render_template('register.html', messages=messages)
        if not request.form.get('password') == request.form.get('confirmation'):
            messages = [{
                'text': 'Password and confirmation must match',
                'class': 'warning'
            }]
            return render_template('register.html', messages=messages)

        # Store new user in Database
        username = request.form.get('username')
        passwordHash = generate_password_hash(request.form.get('password'), method='scrypt:32768:8:1', salt_length=16)
        attempt = processRegistration(username, passwordHash)
        if attempt['success'] == False:
            messages = [{
                'text': 'Username taken',
                'class': 'danger'
                }]
            return render_template('register.html', messages=messages)
        elif attempt['success'] == True:
            session['user_id'] = attempt['id']
            session['username'] = attempt['username']
        
        return redirect(url_for('index'))
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
        data = db.execute('SELECT * FROM users WHERE username = ?', (request.form.get('username'),))
        rows = data.fetchall()
        id = rows[0][0]
        user = rows[0][1]
        hash = rows[0][2]
        print(id, user)
        # Ensure username exists and password is correct
        if user == None:
            # Add message that username not found
            return redirect(url_for('login'))

        if user != request.form.get('username') or not check_password_hash(hash, request.form.get('password')):
            # TODO: pop-up saying username taken
            return render_template('register.html')
        con.close()
        # Remember which user has logged in
        session['user_id'] = id
        session['username'] = user
        print(session)
        # Redirect to My Closet Page
        return redirect(url_for('index'))

    else:
        return render_template('login.html')

@app.route('/mycloset')
@login_required
def mycloset():
    # Get all top-level categories from closets database, submit to be listed as list options
    allcategories = []
    for row in dbSelect('SELECT category FROM clothing GROUP BY category'):
        allcategories.append(row['category'])

    # Get user's categories
    usercategories = []
    for row in dbSelect('SELECT category FROM clothing WHERE userId = ? GROUP BY category', (session['user_id'], )):
        usercategories.append(row['category'])

    # Get user's clothing items
    items = dbSelect('SELECT * FROM clothing WHERE userId = ?', (session['user_id'], ))

    # Get user's materials for new item material datalist
    materials = []
    for row in dbSelect('SELECT * FROM clothing WHERE userId = ? GROUP BY material', (session['user_id'],)):
        materials.append(row['material'])
    
    return render_template('mycloset.html', usercategories=usercategories, items=items, allcategories=allcategories, materials=materials)

@app.route('/logout')
def logout():

    # Forget any user_id
    session.clear()

    # Redirect to home
    return redirect('/')

@app.route('/additem', methods=['POST'])
@login_required
def addItem():
    if request.method != "POST":
        return redirect(url_for('mycloset'))
    
    imagePath = processImageSubmission(request.files)
  
    rowId = createItem(request.form.get('item'), request.form.get('category'), imagePath, session['user_id'], request.form.get('needsPair'), request.form.get('material', ''))

    # Return user to their closet page
    return redirect(url_for('mycloset'))

@app.route('/updateitem', methods=['POST'])
@login_required
def updateItem():
    if request.method != "POST":
        return redirect(url_for('mycloset'))
    
    path = processImageSubmission(request.files)

    itemDetails = {
        'id': request.form.get('itemId'),
        'itemName': request.form.get('item'),
        'category': request.form.get('editCategory'),
        'needsPair': request.form.get('needsPair'),
        'material': request.form.get('material')
    }
    processItemUpdate(itemDetails, path)

    return redirect(url_for('mycloset'))

@app.route('/deleteitem/<int:item_id>')
@login_required
def deleteItem(item_id):
    processItemDeletion(item_id)
    return redirect(url_for('mycloset'))