from flask import Flask, flash, redirect, render_template, request, url_for, jsonify, session, g
from flask_login import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Table, Column, Integer, String, Boolean, Float, ForeignKey, asc, desc, func
import os, re, string, json
import psycopg2
import random

# Constants
#databasePath = os.environ['DATABASE_URL']
databasePath = 'postgres://lbddjnpwrnwrxg:1NUUgEbpLuayk2-41MYqZlFT_2@ec2-23-21-193-224.compute-1.amazonaws.com:5432/d215med6u9hn0v'
debug_mode = True
CROSSWORD_WIDTH = len(string.ascii_lowercase)
MIN_PASSWORD_LENGTH = 3


# Setup the Flask app
app = Flask(__name__, static_folder='static')
app.secret_key = 'A0Zr965464fgfdsN]LWX/,?RT'
app.debug = debug_mode

# Setup for SQLAlchemy
engine = create_engine(databasePath) # Create database engine
# Session class for communication with database. Do not expire on commit so that
# the SQLAlchemy objects can be accessed even after the session is closed
Session = sessionmaker(bind=engine, expire_on_commit=False)
db = Session() # Session instance to be used for all database transactions and queries

# Setup the login manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page.'
login_manager.setup_app(app)

########################################
########################################
####### Flask Routes ###################
########################################
########################################

# Index page - redirect to stories
@app.route('/')
def index():
    return redirect(url_for('home'))

# This function is called before every request
@app.before_request
def before_request():
    # If the user is logged in, set the g.user attribute to the fb_id
    if current_user.is_authenticated():
        g.username = current_user.username

# Close the database connection after each connection is processed
@app.teardown_request
def teardown_request(exception):
    db.close()


###################
# Basic Routes
###################

# Main page
@app.route('/home/')
@login_required
def home():
    return render_template('home.html')


#######################
# User Account Routes
#######################
    
# Login page
@app.route('/login/', methods=['GET', 'POST'])
def login():
    # If the method is POST, try to log the user in
    if request.method == 'POST':
        username = str(request.form.get('username_hidden_input'))
        trace = str(request.form.get('trace_input'))
        
        # If a username, trace, and crossword were not provided
        if username == None or trace == None:
            flash('Login failed!')
            return render_template('login.html')

        # Find the username in the database and retrieve the user object from it
        user = get_user(username)

        # If the trace doesn't match the password/square for the user, then login fails
        if user == None or not user.verifyTrace(trace):
            flash('Incorrect username or trace!')
            return render_template('login.html')

        # Login the user
        login_user(user, remember=True)
        return redirect(url_for('home'))

    # For GET requests, return the login page
    return render_template('login.html')


# Crossword request
@app.route('/login/crossword/<string:username>/')
def crossword(username):
    user = get_user(username)
    if user == None:
        return 'The user <strong>' + username + '</strong> does not exist.'
    return jsonify(user.getCrosswordJSON())


# Logout page
@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Registration page
@app.route('/register/', methods=['GET', 'POST'])
def register():
    # If the method is POST, add the new user if the information is valid
    if request.method == 'POST':
        username = str(request.form['username'])
        password = str(request.form['password'])
        password_confirm = str(request.form['password_confirm'])

        # Get whether the password is valid (True), or the error string if not
        passwordValidOrError = password_is_valid(password)

        # If the username is not a valid format (alphanumeric), flash message and prompt again.
        if not re.match('^[a-zA-Z0-9_.-]+$', username):
            flash('Please enter a valid username. username must consist only of alphanumeric characters')

        # If the username already exists, flash message and prompt again
        elif get_user(username) != None:
            flash('Username already exists')
    
        # If the password and password_confirm do not match
        elif not password == password_confirm:
            flash('Password and confirm password do not match.')

        # If the password does not meet password requirements
        elif not passwordValidOrError == True:
            flash('Please provide a valid password')
            flash(passwordValidOrError)

        # If we get here, the registration is valid and add the user to the database
        # Redirict to login screen with flashed message
        else:
            new_user = User(username, password)
            db.add(new_user)
            db.commit()
            flash('User account for ' + new_user.username + ' created successfully')
            return redirect(url_for('login'))

    # The page is returned for GET and also when the POST request does not successfully create a new user
    return render_template('register.html')


########################################
########################################
####### Database Classes ###############
########################################
########################################

Base = declarative_base() # Base class

# The User class also implements methods reqired for a flask-login user through UserMixin inheritance
class User(Base, UserMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    crosswordJSON = Column(String)
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
    
    def __repr__(self):
        return "<User(username:'%s')>" % (self.username)


    # Return a crossword (the user object saves the currently active crossword in JSON)
    def getCrosswordJSON(self):
        crossword = createCrossword(self.password)
        self.crosswordJSON = json.dumps(crossword)
        db.commit()
        return crossword

    
    # Verify that the trace on the crossword corresponds to the password
    def verifyTrace(self, trace):
        crossword = json.loads(self.crosswordJSON)
        crosswordContent = crossword.get('crosswordContent') # Array of letters
        startX = crossword.get('startX') # Integer
        startY = crossword.get('startY') # Integer
        startHorizontal = crossword.get('startHorizontal') # Boolean
        width = crossword.get('width') # Integer

        if crosswordContent == None or startX == None or startY == None or width == None:
            return False

        if not len(trace) == len(self.password):
            return False

        # Iterate through every part of the trace and make sure that the password is in the traced out part
        prevCoordX = startX
        prevCoordY = startY
        currentHorizontal = startHorizontal
        for i in range(len(trace)):
            traceDirection = trace[i]
            passwordLetter = self.password[i]

            # Make sure the letter matches the current direction
            if ( currentHorizontal and (traceDirection not in ('l','r')) ) or \
                ( (not currentHorizontal) and (traceDirection not in ('u','d')) ):
                return False
            currentHorizontal = not currentHorizontal

            # Find out if the letter is in the trace range.
            # There's a different range for each direction

            # Left
            if traceDirection == "l":
                # Make sure not at left edge
                if prevCoordX == 0:
                    return False
                startIndex = crosswordCoordToIndex(prevCoordY, 0)
                endIndex = crosswordCoordToIndex(prevCoordY, prevCoordX)
                letterRange = crosswordContent[startIndex:endIndex]
                if passwordLetter not in letterRange:
                    return False
                letterIndex = letterRange.index(passwordLetter)
                prevCoordX = letterIndex

            # Right
            elif traceDirection == "r":
                # Make sure not at right edge
                if prevCoordX == CROSSWORD_WIDTH-1:
                    return False
                startIndex = crosswordCoordToIndex(prevCoordY, prevCoordX+1)
                endIndex = crosswordCoordToIndex(prevCoordY+1, 0)
                letterRange = crosswordContent[startIndex:endIndex]
                if passwordLetter not in letterRange:
                    return False
                letterIndex = letterRange.index(passwordLetter)
                prevCoordX = prevCoordX+1 + letterIndex

            # Up
            elif traceDirection == "u":
                # Make sure not at upper edge
                if prevCoordY == 0:
                    return False
                letterRange = []
                for y in xrange(0,prevCoordY):
                    index = crosswordCoordToIndex(y, prevCoordX)
                    letterRange.append(crosswordContent[index])
                if passwordLetter not in letterRange:
                    return False
                letterIndex = letterRange.index(passwordLetter)
                prevCoordY = letterIndex

            # Down
            elif traceDirection == "d":
                # Make sure not at lower edge
                if prevCoordY == CROSSWORD_WIDTH-1:
                    return False
                letterRange = []
                for y in xrange(prevCoordY+1,CROSSWORD_WIDTH):
                    index = crosswordCoordToIndex(y, prevCoordX)
                    letterRange.append(crosswordContent[index])
                if passwordLetter not in letterRange:
                    return False
                letterIndex = letterRange.index(passwordLetter)
                prevCoordY = prevCoordY+1 + letterIndex

            # Invalid direction   
            else:
                return False


        # Reset the currently store crossword
        self.crosswordJSON = None
        db.commit()

        return True

    # Overrides UserMixin default
    # User must be committed to database before get_id returns a valid ID
    def get_id(self):
        return self.id

    

###########################
# Database Access Functions
###########################

# Get the user for a certain ID
def get_user(username):
    return db.query(User).filter(User.username==username).first()

###########################
# Miscellaneous Functions
###########################

# Login/load a user function for session manager
@login_manager.user_loader
def load_user(user_id):
    return db.query(User).filter(User.id==user_id).first()

# Remove HTML tags from string
def remove_html_tags(data):
    p = re.compile(r'<.+?>')
    return p.sub('', data)

# Check that a password is valid
# Returns True if valid
# Returns a string error message if invalid
def password_is_valid(password):
    # Check that the password meets the minimum length requirement
    if len(password) < MIN_PASSWORD_LENGTH:
        return 'password must contain at least ' + str(MIN_PASSWORD_LENGTH) + ' letters'

    # Check that a crossword can be created to match the given password
    if createCrossword(password) == None:
        return 'valid crossword cannot be created from given password'

    # Check that the password only contains lowercase alphabet characters
    # Check that the password does not contain consecutive matching letters
    prevLetter = None
    for char in password:
        if char not in string.ascii_lowercase:
            return 'password must contain only lowercase letters'
        if char == prevLetter:
            return 'password must not have matching consecutive letters'
        prevLetter = char

    # If there are no problems with the password then return True
    return True


# Convert an x,y coord to an index to access the row-major crossword.
# (0, 0) is in the top left
def crosswordCoordToIndex(row, col):
    return row*CROSSWORD_WIDTH + col



# Create a random crossword by looking at the password
# Returns a crossword dictionary with the crossword content, the width, and starting location
# Returns None if a valid crossword cannot be created
def createCrossword(password):
    random.seed()
    size = CROSSWORD_WIDTH
    sequence = [0] * size
    jumbled = [0] * size
    crossword = [0] * (size**2)

    # Fill the crossword with letters
    # Letters must be unique to the row and column
    # Use random Latin square generation technique
    shuffle(jumbled, size)
    for i in range(size):
         sequence[i] = jumbled[i]

    for i in range(size):
        position = sequence[0]
        value = jumbled[position - 1]

        for j in range(size):
            # Place a letter in the crossword corresponding to the value[0:26]
            crossword[crosswordCoordToIndex(j, sequence[j]-1)] = string.ascii_lowercase[value-1]

        rotate(sequence, size)


    # Create a random starting position and direction (horizontal = True/False)
    startHorizontal = (random.randint(0, 1) == 0)
    count = 0
    while True:
        # Make sure the start square is not equal to the first letter of the password
        startX = random.randint(0, CROSSWORD_WIDTH-1);
        startY = random.randint(0, CROSSWORD_WIDTH-1);
        if not crossword[crosswordCoordToIndex(startY, startX)] == password[0]:
            break
        count += 1
        if count > 100:
            return None


    # Return a dictionary with the crossword and the start position
    output = {'crosswordContent' : crossword,
                'width' : CROSSWORD_WIDTH,
                'startX' : startX,
                'startY' : startY,
                'startHorizontal': startHorizontal}
    return output



def shuffle(array1, size):
    for i in range(size):
        array1[i] = i + 1

    for last in range(size, 1, -1):
        rand = random.randint(0, last-1)
        temp = array1[rand]
        array1[rand] = array1[last - 1]
        array1[last - 1] = temp



def rotate(array2, size):
    temp = array2[0];
    for i in range(size-1):
       array2[i] = array2[i+1]
    array2[size - 1] = temp



######################
# Run the application
######################

if __name__ == '__main__':
    # Create the database. This line must come after database class definitions
    Base.metadata.create_all(engine)
    # Run the flask app
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, debug = debug_mode)


