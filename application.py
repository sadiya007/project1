import os, requests
import pdb
import json
import getpass

from werkzeug.security import check_password_hash, generate_password_hash

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import get_goodreads

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
#engine = create_engine(os.getenv("DATABASE_URL"))
engine = create_engine(
    "postgres://htidpfuklxnnyf:ac4404e1db48ddaf2b31f906e8c5d1ade2cb5859dc30da15c7382d77cfcb7453@ec2-52-6-143-153.compute-1.amazonaws.com:5432/den3qj7mugr7k2")
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():

    return render_template("index.html")

@app.route("/openLogin", methods=["POST"])
def openLogin():
    return render_template("login.html")

@app.route("/register", methods=["POST", "GET"])
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
            hashedPassword = generate_password_hash(request.form.get("password"), method="pbkdf2:sha256", salt_length=8)
            db.execute("INSERT INTO userdata (firstname, lastname, username, password) VALUES (:firstname, :lastname, :username, :password)",
            {"firstname": firstname, "lastname": lastname, "username": username, "password": hashedPassword})
            db.commit()
            return render_template("index.html", success_message="You have successfully registered yourself. Please click on Login to proceed.")
        else:
            return render_template("index.html", usernameexists_message="Sorry, that username is taken")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    result = db.execute(
        "SELECT * FROM userdata WHERE username = :username", {"username": username}
    ).fetchone()

    #pdb.set_trace()

    if result == None or not check_password_hash(result['password'], password):
        return render_template(
            "login.html", Invalid_username_message="invalid username and or password"
            )
    else:
        session["user_name"] = username
        session["logged_in"] = True

        return render_template("welcome.html")

@app.route("/search", methods=["POST"])
def search():
    searchqry = request.form.get("search")

    #if len(searchqry) == 0:
        #searchqry = None
    books = db.execute("SELECT * FROM mybooks WHERE (lower(title) LIKE :searchqry) OR (lower(author) LIKE :searchqry) OR (lower(isbn) LIKE :searchqry)",{"searchqry": "%" + searchqry + "%"}).fetchall()
    return render_template("books.html", books=books)

@app.route("/book/<int:book_id>")
def book(book_id):
    book = db.execute("SELECT * FROM mybooks WHERE id = :id", {"id": book_id}).fetchone()
    goodreads = get_goodreads(book.isbn)

    if goodreads.status_code != 200:
        return render_template("error.html", message="404 Error")

    book_all = goodreads.json()
    book_rating = book_all["books"][0]["average_rating"]
    # pdb.set_trace()
    reviews = db.execute("SELECT * FROM reviews LEFT JOIN public.userdata ON (reviews.userdata_id = userdata.id) WHERE mybooks_id = :id",{"id": book_id}).fetchall()
    return render_template("book.html", book=book, book_rating=book_rating, reviews=reviews)

@app.route("/review/<int:mybooks_id>", methods=["POST"])
def review(mybooks_id):
    stars = request.form.get("stars")
    review = request.form.get("review")
    username = session["user_name"]

    users = db.execute("SELECT username, id from userdata WHERE username = :username",{"username": username}).fetchone()

    if (db.execute("SELECT * FROM reviews LEFT JOIN public.userdata ON (reviews.userdata_id = userdata.id) WHERE mybooks_id = :id AND username = :username",{"id": mybooks_id, "username": username},).rowcount > 0):
        return render_template("error.html", message="Review already exists.")
    else:
        db.execute("INSERT INTO reviews (mybooks_id, userdata_id, stars, review) VALUES (:mybooks_id, :userdata_id, :stars, :review)",{"mybooks_id": mybooks_id, "userdata_id": users.id, "stars": stars, "review": review},)
        db.commit()
        return redirect(url_for("book", book_id=mybooks_id))

@app.route("/api/<isbn_id>")
def isbn_api(isbn_id):
    """Return details about a isbn."""

    sadiya = "SELECT * FROM mybooks WHERE isbn = :isbn"
    # Make sure flight exists.
    booksforthisisbn = db.execute(sadiya, {"isbn": isbn_id}).fetchone()

    if booksforthisisbn is None:
        return jsonify({"error": "Invalid ISBN"}), 404

    reviewDataForThisBook = db.execute("select stars from reviews where mybooks_id = :ISBNWALABOOK",{"ISBNWALABOOK": booksforthisisbn.id}).fetchall()


    noOfReviews = 0
    summationOfStars = 0
    for reviewRecord in reviewDataForThisBook:
        summationOfStars = summationOfStars + reviewRecord.stars
        noOfReviews = noOfReviews + 1

    averageRating = 0

    if noOfReviews > 0:
        averageRating = summationOfStars / noOfReviews

    return jsonify({
             "title": booksforthisisbn.title,
             "author": booksforthisisbn.author,
             "year": booksforthisisbn.year,
             "isbn": isbn_id,
             "review_count": noOfReviews,
             "average_score": averageRating
        })

@app.route("/logout", methods=["POST"])
def logout():
    session["user_name"] = None
    session["logged_in"] = False
    session.clear()
    return render_template("index.html")

@app.route("/redirectregister", methods=["POST"])
def redirectregister():
    return render_template("index.html")
