# Flask for Beginners
### A Practical Course Note · Flask 3.x · Python 3.10+
> *From Zero to a Working Web Application — applying the Pareto principle so you learn the 20% of Flask that covers 80% of real-world work.*

---

## Table of Contents

1. [Preface: Why Flask?](#1-preface-why-flask)
2. [Getting Started](#2-getting-started)
3. [Routing & Route Parameters](#3-routing--route-parameters)
4. [Jinja2 Templating](#4-jinja2-templating)
5. [Forms with Flask-WTF](#5-forms-with-flask-wtf)
6. [Flask-SQLAlchemy & Database Connectivity](#6-flask-sqlalchemy--database-connectivity)
7. [Pure JSON Responses — Building an API](#7-pure-json-responses--building-an-api)
8. [Blueprints — Organising Large Apps](#8-blueprints--organising-large-apps)
9. [Session-Based Auth with Flask-Login](#9-session-based-auth-with-flask-login)
10. [JWT Authentication with Flask-JWT-Extended](#10-jwt-authentication-with-flask-jwt-extended)
11. [Essential Supporting Topics](#11-essential-supporting-topics)
12. [Appendix & Quick Reference](#12-appendix--quick-reference)

---

## 1. Preface: Why Flask?

Flask is a **lightweight Python web framework**. It gives you just enough to build web apps and then gets out of your way. Unlike Django (which bundles an ORM, an admin panel, a forms system, and more by default), Flask lets you pick your own tools for each concern. That makes it excellent for learning — you can see exactly what each piece does and why it exists.

By the end of this note you will be able to:

- Serve HTML pages with dynamic data using Jinja2 templates
- Handle URL routing and route parameters
- Build and validate forms with Flask-WTF
- Connect to a database with Flask-SQLAlchemy
- Return JSON responses for REST APIs
- Organise a large app with Blueprints
- Add session-based login with Flask-Login
- Add token-based authentication with Flask-JWT-Extended

> ⚠️ **Prerequisite:** Basic Python (functions, classes, dicts, lists). No prior web framework experience is required.

---

## 2. Getting Started

### 2.1 Project Setup

Always work inside a **virtual environment** so your project's dependencies don't clash with other Python projects on your machine.

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install Flask
pip install flask

# 3. Confirm the installation
flask --version
# Flask 3.x.x  |  Python 3.x.x
```

### 2.2 The Minimal App

```python
# app.py
from flask import Flask

# Flask(__name__) tells Flask where to look for templates and static files.
# __name__ evaluates to the current module's name — just pass it as-is.
app = Flask(__name__)

@app.route('/')          # decorator that registers the URL '/'
def index():
    return 'Hello, World!'

if __name__ == '__main__':
    # debug=True enables auto-reload on code changes and shows
    # an interactive error page in the browser when exceptions occur.
    app.run(debug=True)
```

Run it:

```bash
flask run
# or
python app.py
```

Open `http://127.0.0.1:5000` in your browser and you will see `Hello, World!`.

> ⚠️ **Never use `debug=True` in production.** It exposes an interactive debugger that can execute arbitrary code on your server.

---

### 2.3 The Application Factory Pattern (Recommended)

Putting everything in a single `app.py` works for tiny scripts, but grows unmanageable quickly. The **Application Factory** creates the Flask app inside a function. This allows multiple app instances (critical for testing) and clean extension initialisation.

**Recommended project layout:**

```
myapp/
├── __init__.py       ← create_app() lives here
├── extensions.py     ← db, login_manager, jwt (single source of truth)
├── config.py         ← configuration classes
├── models.py         ← database models
├── auth/
│   ├── __init__.py
│   ├── routes.py     ← auth Blueprint
│   └── forms.py
├── api/
│   ├── __init__.py
│   └── routes.py     ← api Blueprint
├── main/
│   ├── __init__.py
│   └── routes.py     ← main Blueprint
├── templates/
│   ├── base.html
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   └── main/
│       └── index.html
└── static/
    ├── css/
    └── js/
```

```python
# myapp/__init__.py
from flask import Flask
from .extensions import db, login_manager, jwt

def create_app(config='config.DevelopmentConfig'):
    app = Flask(__name__)
    app.config.from_object(config)

    # Initialise extensions (each extension binds itself to the app here)
    db.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)

    # Register blueprints (covered in Module 8)
    from .auth.routes  import auth_bp
    from .main.routes  import main_bp
    from .api.routes   import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    return app
```

```python
# extensions.py
# Define extension objects here WITHOUT an app instance.
# They are bound to a specific app later inside create_app().
from flask_sqlalchemy   import SQLAlchemy
from flask_login        import LoginManager
from flask_jwt_extended import JWTManager

db            = SQLAlchemy()
login_manager = LoginManager()
jwt           = JWTManager()

login_manager.login_view             = 'auth.login'
login_manager.login_message_category = 'warning'
```

```python
# config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()   # reads .env file into os.environ

class Config:
    SECRET_KEY              = os.environ.get('SECRET_KEY', 'dev-fallback')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY          = os.environ.get('JWT_SECRET_KEY', 'jwt-fallback')
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
```

---

## 3. Routing & Route Parameters

### 3.1 Defining Routes

A **route** maps a URL to a Python function (called a *view function*). You define routes with the `@app.route()` decorator.

```python
from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def home():
    return 'Home page'

@app.route('/about')
def about():
    return 'About page'

# Specify which HTTP methods this route accepts (default is GET only)
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        return 'Form submitted!'
    return 'Contact form'
```

### 3.2 Route Parameters

Angle brackets in the URL path **capture a variable segment** and pass it to the view function as a keyword argument.

```python
# <username> becomes a keyword argument named 'username'
@app.route('/user/<username>')
def profile(username):
    return f'Profile of {username}'

# Type converters: int, float, string (default), path, uuid
# Flask converts the captured value and raises 404 if conversion fails
@app.route('/post/<int:post_id>')
def show_post(post_id):
    # post_id is already an int here — no need to call int() yourself
    return f'Post #{post_id}'

# Multiple parameters in one route
@app.route('/category/<string:cat>/item/<int:item_id>')
def show_item(cat, item_id):
    return f'Category: {cat}, Item: {item_id}'

# 'path' converter allows slashes in the value
@app.route('/files/<path:filepath>')
def serve_file(filepath):
    return f'Serving: {filepath}'   # filepath could be 'docs/2025/report.pdf'
```

### 3.3 URL Building with `url_for()`

Hard-coding URLs leads to bugs when you rename routes. **Always use `url_for()`** to generate URLs from function names.

```python
from flask import Flask, url_for, redirect
app = Flask(__name__)

@app.route('/user/<username>')
def profile(username):
    return f'Hello {username}'

@app.route('/go-to-lumi')
def go_to_lumi():
    # url_for generates '/user/lumi' — stays correct even if the route path changes
    return redirect(url_for('profile', username='lumi'))

# In blueprints, prefix with the blueprint name:
# url_for('auth.login')        → /auth/login
# url_for('main.index')        → /
# url_for('static', filename='css/style.css')  → /static/css/style.css
```

### 3.4 The Request Object

Flask exposes the current HTTP request through the `request` proxy object.

```python
from flask import request

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')    # HTML form field
        password = request.form.get('password')
        return f'Logging in {username}'

    # Query string: /login?next=/dashboard
    next_page = request.args.get('next', '/')       # URL parameter

    # JSON body (for API requests)
    data = request.get_json()                        # parses JSON body → dict

    # Uploaded files
    avatar = request.files.get('avatar')             # file upload field

    # Request headers
    token = request.headers.get('Authorization')

    return f'Login form — redirect to {next_page} after login'
```

### 3.5 Redirects & Responses

```python
from flask import redirect, url_for, make_response, abort

# Redirect to another route
return redirect(url_for('main.index'))
return redirect('https://example.com', 301)          # permanent redirect

# Abort with an HTTP error (triggers the matching error handler)
abort(404)    # Not Found
abort(403)    # Forbidden
abort(401)    # Unauthorized

# Custom response with headers
response = make_response('Custom body', 200)
response.headers['X-Custom-Header'] = 'value'
return response
```

---

## 4. Jinja2 Templating

### 4.1 How Templating Works

Templates are HTML files with **Jinja2 syntax**. Flask renders them with `render_template()`, injecting Python variables into the HTML. Flask looks for templates inside the `templates/` folder by default.

```python
# routes.py
from flask import render_template

@app.route('/hello/<name>')
def hello(name):
    posts = [
        {'title': 'First Post', 'body': 'Hello world'},
        {'title': 'Second Post', 'body': 'Flask is great'},
    ]
    # Variables passed as keyword arguments become available in the template
    return render_template('hello.html', name=name, posts=posts, year=2025)
```

```html
{# templates/hello.html #}
{# {# ... #} is a Jinja2 comment — it is not sent to the browser #}

<!DOCTYPE html>
<html lang="en">
<head>
  <title>Hello</title>
</head>
<body>
  {# {{ ... }} outputs a variable — Jinja2 auto-escapes HTML characters #}
  <h1>Hello, {{ name }}!</h1>
  <p>Year: {{ year }}</p>

  {# Use |safe ONLY when you trust the HTML content (e.g., from your own DB) #}
  {# <p>{{ raw_html | safe }}</p> #}
</body>
</html>
```

### 4.2 Control Flow: `if` / `for`

```html
{# templates/posts.html #}

{% if posts %}
  <ul>
    {% for post in posts %}
      {# loop.index starts at 1; loop.index0 starts at 0 #}
      <li>
        <strong>{{ loop.index }}. {{ post.title }}</strong>
        {% if loop.first %} ⭐ Latest{% endif %}
        <p>{{ post.body }}</p>
      </li>
    {% endfor %}
  </ul>
{% else %}
  <p>No posts yet. Be the first to write one!</p>
{% endif %}
```

### 4.3 Template Inheritance (Base Layout)

Instead of copy-pasting the same header/footer into every page, define a **base template** with named blocks, then extend it in child templates.

```html
{# templates/base.html #}
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  {# Child templates can override the title block #}
  <title>{% block title %}My App{% endblock %}</title>

  {# url_for('static', ...) generates the correct URL to your static files #}
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">

  {# Extra head content (scripts, meta tags) can be injected per-page #}
  {% block head %}{% endblock %}
</head>
<body>
  <nav>
    <a href="{{ url_for('main.index') }}">Home</a>
    {% if current_user.is_authenticated %}
      <a href="{{ url_for('auth.logout') }}">Logout ({{ current_user.username }})</a>
    {% else %}
      <a href="{{ url_for('auth.login') }}">Login</a>
    {% endif %}
  </nav>

  {# Flash messages — displayed once then cleared from the session #}
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for category, message in messages %}
      <div class="alert alert-{{ category }}">{{ message }}</div>
    {% endfor %}
  {% endwith %}

  <main>
    {# This is where each page's unique content goes #}
    {% block content %}{% endblock %}
  </main>

  <footer>
    <p>© {{ year }} My App</p>
  </footer>

  {% block scripts %}{% endblock %}
</body>
</html>
```

```html
{# templates/main/index.html — extends the base layout #}
{% extends 'base.html' %}

{% block title %}Home — My App{% endblock %}

{% block content %}
  <h1>Welcome, {{ name }}!</h1>
  <p>This content slot replaces the 'content' block in base.html.</p>

  {# call super() to keep the parent's block content AND add your own #}
  {# {% block scripts %}{{ super() }}<script src="..."></script>{% endblock %} #}
{% endblock %}
```

### 4.4 Jinja2 Filters, Macros & Includes

```html
{# --- Filters: transform a value with the pipe (|) operator --- #}
{{ name  | upper }}              {# LUMI #}
{{ name  | lower }}              {# lumi #}
{{ bio   | truncate(60) }}       {# cuts at 60 chars and adds ... #}
{{ price | round(2) }}           {# 9.99 #}
{{ users | length }}             {# count items in a list #}
{{ date  | strftime('%d %b %Y') }} {# 01 Jan 2025 (with strftime filter) #}

{# --- Set variables inside a template --- #}
{% set greeting = 'Hello' %}
{{ greeting }}, {{ name }}!

{# --- Include a reusable partial --- #}
{% include 'partials/_navbar.html' %}

{# --- Macros: reusable template functions --- #}
{% macro render_field(field) %}
  <div class="form-group">
    {{ field.label }}
    {{ field(class='form-control') }}
    {% for error in field.errors %}
      <span class="error-msg">{{ error }}</span>
    {% endfor %}
  </div>
{% endmacro %}

{# Call it like a function #}
{{ render_field(form.username) }}
{{ render_field(form.email) }}
```

---

## 5. Forms with Flask-WTF

### 5.1 Why Flask-WTF?

Raw HTML forms are trivially easy to fake or manipulate. **Flask-WTF** wraps WTForms to give you:

- **Server-side validation** with clean, declarative rules
- **CSRF protection** — a hidden token prevents cross-site request forgery attacks
- **Pythonic field definitions** — form structure lives in Python, not scattered across HTML

```bash
pip install flask-wtf email-validator
```

### 5.2 Configuration

```python
# config.py — WTForms uses the SECRET_KEY to sign the CSRF token
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-fallback')
    # WTF_CSRF_ENABLED = True  (True by default; set False only for pure JSON APIs)
```

### 5.3 Defining Form Classes

```python
# auth/forms.py
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField,
    BooleanField, TextAreaField, SelectField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Optional, ValidationError
)
from myapp.models import User

class RegisterForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=20)]
    )
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=8)]
    )
    confirm = PasswordField(
        'Confirm Password',
        validators=[EqualTo('password', message='Passwords must match')]
    )
    submit = SubmitField('Create Account')

    # Custom validator — method name must be validate_<fieldname>
    # WTForms calls it automatically during validate_on_submit()
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered.')


class LoginForm(FlaskForm):
    email    = StringField('Email',    validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit   = SubmitField('Log In')
```

### 5.4 Handling the Form in a Route

```python
# auth/routes.py
from flask import render_template, redirect, url_for, flash
from .forms import RegisterForm

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    # validate_on_submit() is True when:
    #   1. The request method is POST, AND
    #   2. All validators pass
    if form.validate_on_submit():
        username = form.username.data
        email    = form.email.data
        password = form.password.data
        # ... hash password, save to DB (see Module 6)
        flash(f'Account created for {username}!', 'success')
        return redirect(url_for('auth.login'))

    # GET request (first visit) → render the empty form
    # POST with errors → render the form with error messages filled in
    return render_template('auth/register.html', form=form)
```

### 5.5 Rendering the Form in Jinja2

```html
{# templates/auth/register.html #}
{% extends 'base.html' %}
{% block title %}Register{% endblock %}

{% block content %}
<h2>Create an Account</h2>

<form method="POST" novalidate>
  {# hidden_tag() renders the CSRF token — NEVER omit this line #}
  {{ form.hidden_tag() }}

  <div class="form-group">
    {{ form.username.label }}
    {{ form.username(class='form-control', placeholder='e.g. lumi123') }}
    {% for error in form.username.errors %}
      <span class="text-danger">{{ error }}</span>
    {% endfor %}
  </div>

  <div class="form-group">
    {{ form.email.label }}
    {{ form.email(class='form-control') }}
    {% for error in form.email.errors %}
      <span class="text-danger">{{ error }}</span>
    {% endfor %}
  </div>

  <div class="form-group">
    {{ form.password.label }}
    {{ form.password(class='form-control') }}
  </div>

  <div class="form-group">
    {{ form.confirm.label }}
    {{ form.confirm(class='form-control') }}
    {% for error in form.confirm.errors %}
      <span class="text-danger">{{ error }}</span>
    {% endfor %}
  </div>

  {{ form.submit(class='btn btn-primary') }}
</form>

<p>Already have an account? <a href="{{ url_for('auth.login') }}">Log in</a></p>
{% endblock %}
```

---

## 6. Flask-SQLAlchemy & Database Connectivity

### 6.1 What is an ORM?

An **Object Relational Mapper (ORM)** lets you interact with your database using Python objects instead of raw SQL strings. Flask-SQLAlchemy wraps SQLAlchemy (Python's most popular ORM) and wires it into the Flask app context automatically.

```bash
pip install flask-sqlalchemy flask-migrate

# For PostgreSQL, also install the database driver:
pip install psycopg2-binary

# For MySQL:
pip install pymysql
```

### 6.2 Configuration

```python
# config.py
class Config:
    # SQLite — no server setup needed, great for development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')

    # PostgreSQL
    # SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost:5432/mydb'

    # MySQL
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password@localhost/mydb'

    SQLALCHEMY_TRACK_MODIFICATIONS = False   # saves memory; suppress a deprecation warning
```

The `db` object is created in `extensions.py` and bound to the app via `db.init_app(app)` inside `create_app()` (shown in Module 2).

### 6.3 Defining Models

Each model class maps to a database table. Each class attribute that is a `db.Column` maps to a table column.

```python
# models.py
from myapp.extensions import db
from datetime import datetime, timezone

# ─── User ────────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'          # explicitly set table name (optional but clear)

    id         = db.Column(db.Integer,     primary_key=True)
    username   = db.Column(db.String(80),  unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)   # store HASH not plaintext
    is_admin   = db.Column(db.Boolean,     default=False)
    created_at = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc))

    # One-to-many: one user can have many posts
    # backref='author' adds a .author attribute to Post objects
    # lazy=True means posts are only loaded from DB when accessed
    posts      = db.relationship('Post', backref='author', lazy=True,
                                 cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'


# ─── Post ────────────────────────────────────────────────────────────────────

class Post(db.Model):
    __tablename__ = 'posts'

    id         = db.Column(db.Integer,     primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    body       = db.Column(db.Text,        nullable=False)
    created_at = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime,    onupdate=lambda: datetime.now(timezone.utc))

    # ForeignKey links this post to exactly one user
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Many-to-many example: a post can have many tags, a tag can belong to many posts
    tags       = db.relationship('Tag', secondary='post_tags', back_populates='posts')


# ─── Tag (many-to-many with Post) ────────────────────────────────────────────

# Association table for the many-to-many relationship
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id',  db.Integer, db.ForeignKey('tags.id'),  primary_key=True),
)

class Tag(db.Model):
    __tablename__ = 'tags'
    id   = db.Column(db.Integer,     primary_key=True)
    name = db.Column(db.String(50),  unique=True, nullable=False)
    posts = db.relationship('Post', secondary='post_tags', back_populates='tags')
```

### 6.4 CRUD Operations

```python
# All DB operations must happen inside an app context.
# Inside a route or CLI command this is automatic.

# ─── CREATE ──────────────────────────────────────────────────────────────────
new_user = User(username='lumi', email='lumi@example.com', password='<hashed>')
db.session.add(new_user)
db.session.commit()      # writes to the database; rolls back on exception

# ─── READ ────────────────────────────────────────────────────────────────────

# Get by primary key — returns None if not found
user = db.session.get(User, 1)

# Filter: .first() returns one object or None
user = User.query.filter_by(username='lumi').first()

# Multiple filters using SQLAlchemy operators
admins = User.query.filter(
    User.is_admin == True,
    User.created_at >= some_date
).all()                   # .all() returns a list

# Order, limit, offset
recent = Post.query.order_by(Post.created_at.desc()).limit(10).all()

# Paginate (returns a Pagination object)
page = Post.query.order_by(Post.created_at.desc()).paginate(page=1, per_page=20)
# page.items  → list of posts on this page
# page.has_next, page.has_prev, page.total

# Count
total_users = User.query.count()

# Eager loading (prevents N+1 query problem)
from sqlalchemy.orm import joinedload
posts_with_author = Post.query.options(joinedload(Post.author)).all()

# ─── UPDATE ──────────────────────────────────────────────────────────────────
user = User.query.filter_by(username='lumi').first()
user.email = 'newemail@example.com'
db.session.commit()        # SQLAlchemy detects the change automatically

# ─── DELETE ──────────────────────────────────────────────────────────────────
user = db.session.get(User, 1)
db.session.delete(user)
db.session.commit()
```

> ⚠️ **Always wrap DB operations in try/except in production:**
> ```python
> try:
>     db.session.add(obj)
>     db.session.commit()
> except Exception as e:
>     db.session.rollback()
>     raise e
> ```

### 6.5 Database Migrations with Flask-Migrate

`db.create_all()` creates tables from scratch but **cannot alter existing tables**. When you change a model (add a column, rename a field), you need migrations. Flask-Migrate uses Alembic under the hood.

```bash
# One-time setup
flask db init          # creates a migrations/ folder — commit this to git

# Every time you change a model:
flask db migrate -m "add is_admin column to users"   # auto-detects changes
flask db upgrade       # applies the migration to the database

# Roll back the last migration
flask db downgrade

# See migration history
flask db history
```

```python
# __init__.py — wire up Flask-Migrate
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)
    ...
    migrate = Migrate(app, db)
    ...
    return app
```

---

## 7. Pure JSON Responses — Building an API

### 7.1 `jsonify()` Basics

Flask's `jsonify()` converts a Python dict or list to a proper JSON HTTP response with `Content-Type: application/json`.

```python
from flask import Flask, jsonify, request, abort
app = Flask(__name__)

# Dummy data (replace with real DB queries)
books = [
    {'id': 1, 'title': 'Things Fall Apart', 'author': 'Chinua Achebe'},
    {'id': 2, 'title': 'Purple Hibiscus',   'author': 'Chimamanda Adichie'},
]

@app.route('/api/books', methods=['GET'])
def get_books():
    return jsonify(books), 200                 # 200 OK

@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = next((b for b in books if b['id'] == book_id), None)
    if book is None:
        return jsonify({'error': 'Book not found'}), 404
    return jsonify(book), 200
```

### 7.2 Accepting JSON Input

```python
@app.route('/api/books', methods=['POST'])
def create_book():
    # get_json() parses the request body — returns None if Content-Type is wrong
    # or silent=True to suppress errors
    data = request.get_json(silent=True)

    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    if 'title' not in data:
        return jsonify({'error': '`title` field is required'}), 422

    new_book = {
        'id':     len(books) + 1,
        'title':  data['title'],
        'author': data.get('author', 'Unknown'),
    }
    books.append(new_book)
    return jsonify(new_book), 201              # 201 Created
```

### 7.3 Standardised Response Envelope

A **consistent response shape** makes your API far easier for frontend developers to consume. Define helper functions once and use them everywhere.

```python
# api/utils.py
from flask import jsonify

def success(data=None, message='OK', status=200):
    return jsonify({
        'status':  'success',
        'message': message,
        'data':    data,
    }), status

def error(message='An error occurred', status=400, errors=None):
    body = {
        'status':  'error',
        'message': message,
        'data':    None,
    }
    if errors:
        body['errors'] = errors     # field-level validation errors
    return jsonify(body), status
```

```python
# Usage in routes
from .utils import success, error
from myapp.models import User

@api_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return error('User not found', 404)
    return success({
        'id':       user.id,
        'username': user.username,
        'email':    user.email,
    })
```

### 7.4 Global JSON Error Handlers

Register these so that 404 and 500 errors return JSON — not Flask's default HTML error pages.

```python
# __init__.py or errors.py
@app.errorhandler(400)
def bad_request(e):
    return jsonify({'status': 'error', 'message': 'Bad request'}), 400

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({'status': 'error', 'message': 'Authentication required'}), 401

@app.errorhandler(403)
def forbidden(e):
    return jsonify({'status': 'error', 'message': 'Forbidden'}), 403

@app.errorhandler(404)
def not_found(e):
    return jsonify({'status': 'error', 'message': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
```

### 7.5 Serialising SQLAlchemy Models

SQLAlchemy model objects cannot be passed directly to `jsonify()`. Add a `to_dict()` method to your models.

```python
# models.py
class User(db.Model):
    ...

    def to_dict(self, include_email=False):
        data = {
            'id':         self.id,
            'username':   self.username,
            'created_at': self.created_at.isoformat(),
        }
        if include_email:
            data['email'] = self.email
        return data


class Post(db.Model):
    ...

    def to_dict(self):
        return {
            'id':         self.id,
            'title':      self.title,
            'body':       self.body,
            'created_at': self.created_at.isoformat(),
            'author':     self.author.username,   # uses the backref
        }
```

```python
# In a route:
@api_bp.route('/users')
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users]), 200
```

---

## 8. Blueprints — Organising Large Apps

### 8.1 The Problem Blueprints Solve

When all your routes live in `app.py`, the file becomes unmanageable. Blueprints let you split routes into **feature-based modules** (auth, posts, admin, API) and register them on the main app — similar to how Django separates code into apps.

### 8.2 Creating a Blueprint

```python
# auth/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from myapp.extensions import db
from myapp.models import User
from .forms import LoginForm, RegisterForm

# 'auth' is the blueprint's name — used as prefix when calling url_for()
# url_prefix='/auth' prepends /auth to ALL routes defined in this blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))   # 'auth.login' = blueprint.function
    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
```

```python
# main/routes.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from myapp.models import Post

main_bp = Blueprint('main', __name__)   # no url_prefix → routes at root /

@main_bp.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    return render_template('main/index.html', posts=posts)

@main_bp.route('/dashboard')
@login_required                         # redirects to auth.login if not logged in
def dashboard():
    return render_template('main/dashboard.html', user=current_user)
```

```python
# api/routes.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from myapp.models import Post

api_bp = Blueprint('api', __name__)     # url_prefix added at registration time

@api_bp.route('/posts')
def list_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return jsonify([p.to_dict() for p in posts]), 200
```

### 8.3 Registering Blueprints in the Factory

```python
# myapp/__init__.py
def create_app():
    app = Flask(__name__)
    ...

    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .api.routes  import api_bp

    app.register_blueprint(auth_bp)                      # /auth/login, /auth/logout ...
    app.register_blueprint(main_bp)                      # /, /dashboard ...
    app.register_blueprint(api_bp, url_prefix='/api/v1') # /api/v1/posts ...

    return app
```

### 8.4 Blueprint-Specific Templates & Static Files

```python
# A blueprint can have its own templates folder
auth_bp = Blueprint(
    'auth',
    __name__,
    url_prefix='/auth',
    template_folder='templates',   # relative to this blueprint's folder
    static_folder='static',
)
# Flask first searches the app-level templates/, then the blueprint's templates/
```

---

## 9. Session-Based Auth with Flask-Login

### 9.1 How Session Auth Works

When a user logs in, Flask stores their user ID in a **signed cookie** (the session). On every subsequent request, Flask reads the cookie to identify the user. Flask-Login manages all of this — loading the user object, protecting routes, and providing `current_user`.

```bash
pip install flask-login
pip install bcrypt          # or: pip install werkzeug (already installed with Flask)
```

### 9.2 The User Model

```python
# models.py
from myapp.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# UserMixin adds four required properties Flask-Login expects:
# is_authenticated, is_active, is_anonymous, get_id()
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id       = db.Column(db.Integer,     primary_key=True)
    username = db.Column(db.String(80),  unique=True, nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean,   default=True)  # set False to "soft ban" a user

    def set_password(self, plaintext: str):
        # Werkzeug uses PBKDF2-SHA256 by default — strong enough for most apps
        self.password = generate_password_hash(plaintext)

    def check_password(self, plaintext: str) -> bool:
        return check_password_hash(self.password, plaintext)

    def __repr__(self):
        return f'<User {self.username}>'


# Flask-Login calls this function to reload a User from its ID stored in the session.
# Must be registered on the login_manager object.
@login_manager.user_loader
def load_user(user_id: str):
    # user_id comes from the session cookie as a string — convert to int
    return db.session.get(User, int(user_id))
```

### 9.3 Protecting Routes & Using `current_user`

```python
from flask_login import login_required, current_user

# @login_required redirects unauthenticated users to login_manager.login_view
@main_bp.route('/dashboard')
@login_required
def dashboard():
    # current_user is the logged-in User object
    # (or an AnonymousUser if not authenticated)
    return render_template('dashboard.html', user=current_user)

@main_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # Only allow users to edit their own profile
    ...
```

```html
{# In any template — current_user is available globally #}
{% if current_user.is_authenticated %}
  <p>Welcome back, {{ current_user.username }}!</p>
  <a href="{{ url_for('auth.logout') }}">Logout</a>
{% else %}
  <a href="{{ url_for('auth.login') }}">Login</a>
  <a href="{{ url_for('auth.register') }}">Register</a>
{% endif %}
```

### 9.4 Role-Based Access (Simple Pattern)

```python
# models.py — add a role column
class User(UserMixin, db.Model):
    ...
    role = db.Column(db.String(20), default='user')   # 'user' | 'admin'

    @property
    def is_admin(self):
        return self.role == 'admin'


# A simple decorator for admin-only routes
from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# Usage
@admin_bp.route('/admin/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)
```

---

## 10. JWT Authentication with Flask-JWT-Extended

### 10.1 Session Auth vs JWT

| | Session Auth (Flask-Login) | JWT Auth (Flask-JWT-Extended) |
|---|---|---|
| State stored | Server (session cookie) | Client (token) |
| Best for | Server-rendered HTML apps | REST APIs / mobile clients |
| Scales across servers | Needs shared session store | Yes — stateless |
| Logout | Delete session on server | Invalidate token (requires blocklist) |

```bash
pip install flask-jwt-extended
```

### 10.2 Setup

JWT config was already covered in the `Config` class (Module 2). Add the `jwt` extension to `extensions.py` and call `jwt.init_app(app)` in `create_app()`.

### 10.3 Login & Token Issuance

```python
# api/auth_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from myapp.models import User

api_auth = Blueprint('api_auth', __name__, url_prefix='/api/auth')

@api_auth.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'msg': 'JSON body required'}), 400

    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({'msg': 'Email already registered'}), 409

    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'msg': 'Account created', 'id': user.id}), 201


@api_auth.route('/login', methods=['POST'])
def login():
    data     = request.get_json(silent=True)
    email    = data.get('email')    if data else None
    password = data.get('password') if data else None

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'msg': 'Invalid email or password'}), 401

    # The 'identity' is embedded inside the token — typically the user's primary key.
    # Do NOT put sensitive data (passwords, full email) in the token payload.
    access_token  = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        'access_token':  access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(include_email=True),
    }), 200
```

### 10.4 Protecting API Endpoints

```python
from flask_jwt_extended import jwt_required, get_jwt_identity

# @jwt_required() expects: Authorization: Bearer <access_token>
@api_auth.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()          # extracts the identity from the token
    user    = db.session.get(User, user_id)
    if not user:
        return jsonify({'msg': 'User not found'}), 404
    return jsonify(user.to_dict(include_email=True)), 200


@api_bp.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    user_id = get_jwt_identity()
    data    = request.get_json(silent=True)

    post = Post(title=data['title'], body=data['body'], user_id=user_id)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict()), 201
```

### 10.5 Refreshing Access Tokens

Access tokens are short-lived (1 hour). Refresh tokens are long-lived (30 days). When the access token expires, the client uses the refresh token to get a new one — without asking the user to log in again.

```python
@api_auth.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)          # requires the REFRESH token, not the access token
def refresh():
    user_id    = get_jwt_identity()
    new_access = create_access_token(identity=user_id)
    return jsonify({'access_token': new_access}), 200
```

### 10.6 Token Revocation (Logout)

JWTs cannot be "deleted" like sessions, but you can maintain a blocklist of revoked token IDs (JTI).

```python
# A simple in-memory blocklist (use Redis in production)
revoked_tokens = set()

from myapp.extensions import jwt

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return jwt_payload['jti'] in revoked_tokens

@api_auth.route('/logout', methods=['DELETE'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']       # unique identifier of the current token
    revoked_tokens.add(jti)
    return jsonify({'msg': 'Token revoked — logged out'}), 200
```

### 10.7 Client-Side Token Flow

```
1. POST /api/auth/login  { email, password }
   ← 200 { access_token, refresh_token }

2. Store tokens (memory > localStorage for security)

3. GET /api/auth/me
   Header: Authorization: Bearer <access_token>
   ← 200 { user data }

4. When access_token expires (401 Unauthorized):
   POST /api/auth/refresh
   Header: Authorization: Bearer <refresh_token>
   ← 200 { new access_token }

5. DELETE /api/auth/logout
   Header: Authorization: Bearer <access_token>
   ← 200 { logged out }
```

---

## 11. Essential Supporting Topics

### 11.1 Environment Variables & `.env`

Never hard-code secrets in your source code. Use environment variables.

```bash
pip install python-dotenv
```

```bash
# .env  ← ADD THIS TO .gitignore IMMEDIATELY
SECRET_KEY=replace-with-64-random-chars
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
JWT_SECRET_KEY=another-long-random-string
```

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()   # reads .env into os.environ at import time

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-fallback-not-for-production'
```

> ⚠️ **Generating a strong secret key:**
> ```python
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### 11.2 Static Files

```python
# Flask serves files from the static/ folder at /static/...
# Reference them in templates with url_for() — never hard-code paths
```

```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
<script src="{{ url_for('static', filename='js/main.js') }}"></script>
<img src="{{ url_for('static', filename='images/logo.png') }}" alt="Logo">
```

### 11.3 Flash Messages

Flash messages are **one-time notifications** stored in the session. They disappear after being displayed once.

```python
from flask import flash

# In any route — categories map to CSS classes (success/danger/info/warning)
flash('Profile updated!', 'success')
flash('Invalid input. Please try again.', 'danger')
flash('You have a new message.', 'info')
```

```html
{# In base.html — display all pending flashes #}
{% with messages = get_flashed_messages(with_categories=true) %}
  {% for category, message in messages %}
    <div class="alert alert-{{ category }}" role="alert">
      {{ message }}
    </div>
  {% endfor %}
{% endwith %}
```

### 11.4 CORS for API Projects

Browsers block JavaScript on one domain from calling your API on another unless you explicitly allow it (Cross-Origin Resource Sharing).

```bash
pip install flask-cors
```

```python
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    ...

    # Allow all origins — fine for development
    CORS(app)

    # Production: restrict to specific origins and paths
    # CORS(app, resources={
    #     r'/api/*': {
    #         'origins': ['https://myfrontend.com', 'https://www.myfrontend.com'],
    #         'methods': ['GET', 'POST', 'PUT', 'DELETE'],
    #         'allow_headers': ['Content-Type', 'Authorization'],
    #     }
    # })
    ...
    return app
```

### 11.5 File Uploads

```python
import os
from flask import request, current_app
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        return error('No file part', 400)

    file = request.files['file']
    if file.filename == '':
        return error('No file selected', 400)

    if file and allowed_file(file.filename):
        # secure_filename strips dangerous characters from the filename
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        file.save(os.path.join(upload_dir, filename))
        return success({'filename': filename}, status=201)

    return error('File type not allowed', 415)
```

```python
# config.py — limit upload size
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024   # 16 MB max
```

### 11.6 Useful CLI Commands

```bash
# Run the dev server
flask run
flask run --port 8080 --debug

# Open an interactive Python shell with the app context pre-loaded
# — great for one-off DB queries and debugging
flask shell
>>> from myapp.models import User
>>> User.query.all()
>>> from myapp.extensions import db
>>> db.session.get(User, 1)

# Database migrations
flask db init                              # run once
flask db migrate -m "short description"   # generate migration
flask db upgrade                          # apply migration
flask db downgrade                        # roll back one migration
flask db history                          # show migration history
flask db current                          # show which migration is applied

# Run a custom CLI command (define your own)
# @app.cli.command('seed-db')
# def seed_db(): ...
flask seed-db
```

### 11.7 Testing Flask Apps

```bash
pip install pytest
```

```python
# tests/conftest.py
import pytest
from myapp import create_app
from myapp.extensions import db as _db

@pytest.fixture
def app():
    app = create_app('config.TestingConfig')
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()


# tests/test_auth.py
def test_register(client):
    response = client.post('/auth/register', data={
        'username': 'testuser',
        'email':    'test@example.com',
        'password': 'password123',
        'confirm':  'password123',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Account created' in response.data

def test_api_login(client):
    # First create a user, then test the API login
    response = client.post('/api/auth/login',
        json={'email': 'test@example.com', 'password': 'password123'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
```

```python
# config.py
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # in-memory DB, wiped after each test
    WTF_CSRF_ENABLED = False                         # disable CSRF for form testing
```

---

## 12. Appendix & Quick Reference

### HTTP Status Codes

| Code | Meaning | When to use |
|------|---------|-------------|
| `200` | OK | Successful GET, PUT, PATCH |
| `201` | Created | Successful POST that created a resource |
| `204` | No Content | Successful DELETE (no body) |
| `400` | Bad Request | Malformed request / missing required fields |
| `401` | Unauthorized | Not authenticated — missing or invalid token |
| `403` | Forbidden | Authenticated but not permitted |
| `404` | Not Found | Resource does not exist |
| `405` | Method Not Allowed | Wrong HTTP method for this endpoint |
| `409` | Conflict | Duplicate resource (e.g., email already registered) |
| `422` | Unprocessable Entity | Valid JSON, but semantically invalid data |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Unexpected server exception |

---

### Packages Cheat Sheet

| Package | Purpose | Install |
|---------|---------|---------|
| `flask` | Core web framework | `pip install flask` |
| `flask-wtf` | Form validation + CSRF | `pip install flask-wtf` |
| `flask-sqlalchemy` | ORM / database layer | `pip install flask-sqlalchemy` |
| `flask-migrate` | DB schema migrations | `pip install flask-migrate` |
| `flask-login` | Session-based auth | `pip install flask-login` |
| `flask-jwt-extended` | JWT token auth | `pip install flask-jwt-extended` |
| `flask-cors` | Cross-Origin Resource Sharing | `pip install flask-cors` |
| `python-dotenv` | Load `.env` variables | `pip install python-dotenv` |
| `email-validator` | Email field validation | `pip install email-validator` |
| `bcrypt` / `werkzeug` | Password hashing | `pip install bcrypt` |
| `psycopg2-binary` | PostgreSQL adapter | `pip install psycopg2-binary` |
| `pymysql` | MySQL adapter | `pip install pymysql` |
| `pytest` | Testing framework | `pip install pytest` |

---

### Common Mistakes to Avoid

| Mistake | Fix |
|---------|-----|
| Storing plain-text passwords | Always use `generate_password_hash()` or bcrypt |
| Hard-coding `SECRET_KEY` in source | Load from environment variable |
| Forgetting `{{ form.hidden_tag() }}` | CSRF token is required in every POST form |
| Using `db.create_all()` to alter tables | Use Flask-Migrate for any schema changes |
| Returning SQLAlchemy objects directly in `jsonify()` | Add a `to_dict()` method to your models |
| Missing `@login_required` on sensitive routes | Audit every route that touches user data |
| `debug=True` in production | Always `False` in production |
| Committing migrations/ folder with broken scripts | Test migrations on a copy of prod DB first |

---

### What to Learn Next

Once you are comfortable with everything in this note, here is a natural progression:

1. **Pagination** — `query.paginate()` + page controls in templates
2. **Email sending** — Flask-Mail or Resend for transactional email
3. **Celery + Redis** — background task queues (sending emails, processing uploads)
4. **Rate limiting** — Flask-Limiter to protect API endpoints from abuse
5. **File storage** — AWS S3 / Cloudinary for storing user-uploaded files
6. **Caching** — Flask-Caching with Redis to speed up expensive queries
7. **WebSockets** — Flask-SocketIO for real-time features (chat, notifications)
8. **Deployment** — Gunicorn + Nginx on a VPS, or Render / Railway for managed hosting
9. **Docker** — containerise your Flask app for consistent deployments
10. **API documentation** — Flask-RESTX or Flasgger (Swagger UI auto-generation)

---

# Flask-WTF & Forms in Flask — A Beginner's Guide

## 1. What Problem Do Forms Solve?

In any web application, forms are how users send data to the server — login credentials, registration info, search queries, contact messages, etc. Flask, being a micro-framework, doesn't ship with form handling out of the box. That's where **Flask-WTF** comes in.

---

## 2. The Players Involved

| Package | Role |
|---|---|
| `WTForms` | Core library — defines form fields, validators, and rendering |
| `Flask-WTF` | Flask integration layer — adds CSRF protection, Flask config binding, file upload helpers |

You always install both, but you mostly interact with `Flask-WTF`.

```bash
pip install flask-wtf
```

---

## 3. What is CSRF and Why Does It Matter?

**CSRF (Cross-Site Request Forgery)** is an attack where a malicious site tricks a logged-in user's browser into submitting a form to *your* server without their knowledge.

Flask-WTF protects against this by embedding a **hidden token** in every form. When the form is submitted, Flask-WTF verifies the token before processing the data. If the token is missing or wrong, the request is rejected.

To enable CSRF protection, your Flask app needs a secret key:

```python
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
```

> ⚠️ Never hardcode your secret key in production. Use environment variables.

---

## 4. Anatomy of a Flask-WTF Form

A form is a Python class that inherits from `FlaskForm`. Each field is a class attribute.

```python
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    email    = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit   = SubmitField('Log In')
```

### Breaking it down

- **`FlaskForm`** — base class from Flask-WTF
- **`StringField`, `PasswordField`, `SubmitField`** — field types from WTForms
- **`validators`** — a list of rules the field's value must pass before the form is considered valid
- The first argument to each field (e.g. `'Email'`) is the **label** — what shows up in the HTML

---

## 5. Common Field Types

| Field | Use Case |
|---|---|
| `StringField` | Any single-line text input |
| `PasswordField` | Password input (masked) |
| `TextAreaField` | Multi-line text |
| `EmailField` | Email with basic format validation |
| `IntegerField` | Numeric input |
| `BooleanField` | Checkbox (True/False) |
| `SelectField` | Dropdown — requires a `choices` list |
| `FileField` | File uploads (Flask-WTF provides `FileField`) |
| `SubmitField` | Submit button |
| `HiddenField` | Hidden input (not visible to user) |

---

## 6. Common Validators

Validators live in `wtforms.validators`. You pass them as a list to the `validators=` argument.

| Validator | What It Checks |
|---|---|
| `DataRequired()` | Field must not be empty |
| `Email()` | Must be a valid email format |
| `Length(min=n, max=n)` | String length constraints |
| `EqualTo('field_name')` | Must match another field (e.g., confirm password) |
| `NumberRange(min=n, max=n)` | Numeric value constraints |
| `Optional()` | Makes the field optional (skips other validators if empty) |
| `Regexp(r'pattern')` | Must match a regex pattern |
| `URL()` | Must be a valid URL |

Example — a registration form with password confirmation:

```python
from wtforms.validators import DataRequired, Email, Length, EqualTo

class RegisterForm(FlaskForm):
    username         = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email            = StringField('Email', validators=[DataRequired(), Email()])
    password         = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit           = SubmitField('Register')
```

---

## 7. Using the Form in a View

```python
from flask import Flask, render_template, redirect, url_for, flash
from forms import LoginForm  # your form class

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret'

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        # Form was submitted AND all validators passed
        email = form.email.data
        password = form.password.data
        # ... authenticate the user
        flash('Logged in successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html', form=form)
```

### What `validate_on_submit()` does

It's a convenience method that returns `True` only if:

1. The request method is `POST` (or `PUT`/`PATCH`)
2. All validators pass
3. The CSRF token is valid

On a `GET` request, it returns `False` — so the empty form is just rendered.

---

## 8. Rendering the Form in a Template (Jinja2)

Flask-WTF forms are passed to templates and rendered using Jinja2.

**Manual rendering (most control):**

```html
<!-- templates/login.html -->
<form method="POST" action="">
    {{ form.hidden_tag() }}  <!-- ← This renders the CSRF token. NEVER forget this. -->

    <div>
        {{ form.email.label }}
        {{ form.email(placeholder="you@example.com") }}
        {% for error in form.email.errors %}
            <span style="color: red;">{{ error }}</span>
        {% endfor %}
    </div>

    <div>
        {{ form.password.label }}
        {{ form.password() }}
        {% for error in form.password.errors %}
            <span style="color: red;">{{ error }}</span>
        {% endfor %}
    </div>

    {{ form.submit() }}
</form>
```

> **`{{ form.hidden_tag() }}`** renders the CSRF hidden input. Without it, every POST will return a `400 Bad Request`.

You can pass HTML attributes directly to field calls:

```html
{{ form.email(class="form-control", placeholder="Enter email") }}
```

---

## 9. Accessing and Displaying Validation Errors

After a failed submission, `form.<field>.errors` holds a list of error messages:

```html
{% if form.username.errors %}
    {% for error in form.username.errors %}
        <p class="error">{{ error }}</p>
    {% endfor %}
{% endif %}
```

You can also access all errors at once:

```python
# In your view, for debugging:
print(form.errors)
# {'email': ['Invalid email address.'], 'password': ['Field must be at least 6 characters long.']}
```

---

## 10. Custom Validators

Sometimes built-in validators aren't enough. You can add a custom validator as a method on the form class. Flask-WTF will automatically call any method named `validate_<fieldname>`:

```python
from wtforms import ValidationError
from models import User  # hypothetical

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    # ...

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username is already taken.')
```

If the username exists in the database, the form will fail validation and surface the error message just like a built-in validator would.

---

## 11. File Uploads with Flask-WTF

Flask-WTF provides a `FileField` with file-type validation:

```python
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SubmitField

class UploadForm(FlaskForm):
    photo  = FileField('Profile Photo', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Upload')
```

In your view, handle the file with `request.files` or `form.photo.data`:

```python
from werkzeug.utils import secure_filename
import os

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.photo.data
        filename = secure_filename(file.filename)
        file.save(os.path.join('uploads', filename))
        return 'File uploaded!'
    return render_template('upload.html', form=form)
```

> Your HTML form tag must include `enctype="multipart/form-data"` for file uploads to work.

---

## 12. The Full Request Lifecycle — Visualized

```
User visits /login (GET)
    ↓
View creates LoginForm()
    ↓
validate_on_submit() → False (GET request)
    ↓
render_template('login.html', form=form)
    ↓
User fills form, clicks Submit (POST)
    ↓
View creates LoginForm() again (now populated with request.form data)
    ↓
validate_on_submit() → checks CSRF + all validators
    ├── FAIL → re-render template with errors on form object
    └── PASS → process data, redirect
```

> The **POST → redirect → GET** pattern (PRG) is the standard approach. Redirecting after a successful POST prevents duplicate form submissions if the user refreshes the page.

---

## 13. Quick Reference Cheatsheet

```python
# 1. Install
pip install flask-wtf

# 2. Config
app.config['SECRET_KEY'] = 'your-secret'

# 3. Define form
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class MyForm(FlaskForm):
    name   = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Submit')

# 4. Use in view
form = MyForm()
if form.validate_on_submit():
    data = form.name.data  # access submitted value
    return redirect(url_for('success'))
return render_template('form.html', form=form)

# 5. In template
# <form method="POST">
#   {{ form.hidden_tag() }}   ← CSRF token, never omit
#   {{ form.name.label }}
#   {{ form.name() }}
#   {% for e in form.name.errors %}<span>{{ e }}</span>{% endfor %}
#   {{ form.submit() }}
# </form>
```

---

## 14. Common Beginner Mistakes

| Mistake | Fix |
|---|---|
| Forgetting `{{ form.hidden_tag() }}` | Always include it — causes `400` errors without it |
| Not setting `SECRET_KEY` | CSRF will fail silently or raise a cryptic error |
| Using `form.validate()` instead of `form.validate_on_submit()` | `validate()` alone doesn't check request method |
| Not passing `methods=['GET', 'POST']` to the route | POST requests will return `405 Method Not Allowed` |
| Forgetting `enctype="multipart/form-data"` on file upload forms | Files won't be received by Flask |
| Accessing `form.field.data` before `validate_on_submit()` returns `True` | Data may be `None` or unvalidated |

---

