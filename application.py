import os

from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine, text
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
    return redirect(url_for("login"))



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not username or not password:
        return render_template("register.html", error="Username and password required.")

    # Check if username exists
    existing = db.execute(
        text("SELECT id FROM users WHERE username = :u"),
        {"u": username}
    ).fetchone()

    if existing:
        return render_template("register.html", error="Username already taken.")

    # Insert user
    db.execute(
        text("INSERT INTO users (username, password) VALUES (:u, :p)"),
        {"u": username, "p": password}
    )
    db.commit()

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    user = db.execute(
        text("SELECT id, password FROM users WHERE username = :u"),
        {"u": username}
    ).fetchone()

    if user is None or user.password != password:
        return render_template("login.html", error="Invalid username or password.")

    session["user_id"] = user.id
    return redirect(url_for("search"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def require_login():
    return session.get("user_id") is not None


@app.route("/search", methods=["GET", "POST"])
def search():
    if not require_login():
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("search.html")

    q = request.form.get("q", "").strip()
    if not q:
        return render_template("search.html", error="Enter a search term.")

    like = f"%{q}%"
    books = db.execute(
        text("""
            SELECT isbn, title, author, year
            FROM books
            WHERE isbn ILIKE :like
               OR title ILIKE :like
               OR author ILIKE :like
            ORDER BY title
            LIMIT 50
        """),
        {"like": like}
    ).fetchall()

    return render_template("search.html", books=books, q=q)


@app.route("/book/<string:isbn>")
def book(isbn):
    if not require_login():
        return redirect(url_for("login"))

    book_row = db.execute(
        text("SELECT isbn, title, author, year FROM books WHERE isbn = :isbn"),
        {"isbn": isbn}
    ).fetchone()

    if book_row is None:
        return "Book not found", 404

    return render_template("book.html", book=book_row)
