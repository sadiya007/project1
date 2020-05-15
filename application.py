import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/openLogin", methods=["POST"])
def openLogin():
    return render_template("login.html")

@app.route("/register", methods=["POST"])
def register():
    """Help us register yourselves."""

    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    username = request.form.get("username")
    password = request.form.get("password")

    # Check if fields are empty
    if not firstname or not lastname or not username or not password:
        return render_template("index.html", fieldempty_message="Please enter all fields")

    else:
        #Check if username already exists
        existingUser = db.execute("SELECT * FROM userdata where upper(username) = upper(:username)",{"username": username}).fetchone()
        if existingUser is None:
            db.execute("INSERT INTO userdata (firstname, lastname, username, password) VALUES (:firstname, :lastname, :username, :password)",
            {"firstname": firstname, "lastname": lastname, "username": username, "password": password})
            db.commit()
            return render_template("index.html", success_message="You have successfully registered yourself. Please click on Login to proceed.")
        else:
            return render_template("index.html", usernameexists_message="Sorry, that username is taken")

@app.route("/login", methods=["POST"])
def login():
    #login page
    #return render_template("login.html")
    username = request.form.get("username")
    password = request.form.get("password")
    if db.execute("SELECT * FROM userdata WHERE username = :username AND password = :password" , {"username": username, "password": password}).rowcount == 0:
        return render_template("login.html", Invalid_username_message="Invalid Username and or password.")
    else:
        return render_template("welcome.html")

    
