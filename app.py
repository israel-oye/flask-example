import os
import json
import threading
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, abort, flash, jsonify, redirect, session, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_mail import Mail, Message
from flask_migrate import Migrate
import requests
from werkzeug.security import check_password_hash, generate_password_hash

from db import db
from forms import LoginForm, PostForm, RegisterForm
from models import OTPToken, Post, User
from utils import generate_random_otp, send_registration_mail

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URI")
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = os.getenv("DEFAULT_EMAIL")
app.config["MAIL_PASSWORD"] = os.getenv("EMAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("DEFAULT_EMAIL")


mail = Mail(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "danger"

db.init_app(app)
migrate = Migrate(app, db, render_as_batch=True)

with app.app_context():
    db.create_all()


OTP_LIFESPAN_MINUTES = 10

@login_manager.user_loader
def get_user(pk):
    return User.query.filter_by(id=int(pk)).first()

@app.route('/')
def index():
    print(request.headers)
    return render_template("index.html")


@app.route('/send-email', methods=['GET', 'POST'])
def send_email():
    if request.method == 'POST':
        email = request.form.get('email')
        msg = Message(
            subject="Testing mail from Flask",
            body="Hello world. I'm testing my email",
            recipients=[email]
        )

        mail.send(message=msg)

        return f"Mail sent to {email}"

    return render_template("send-email.html")


@app.get('/users')
def users():
    user = User(email='ioyeboade@gmail.com', password='Password123')
    db.session.add(user)
    db.session.commit()

    users = User.query.all()
    return str(users)


@app.get('/users/<id>')
def fetch_user(id):
    user = User.query.filter_by(id=id).first()

    if not user:
        return jsonify({
            "message": "User not found"
        })
    
    return jsonify({
        "id": user.id,
        "name": user.username
    })


@app.route('/dashboard')
@login_required
def dashboard():
    print(current_user.is_authenticated)
    return render_template('dashboard.html', user=current_user)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.lower()
        password = form.password.data

        user: User = User.query.filter_by(email=email).first()
        if user is None:
            flash("Invalid email", category="danger")
        else:
            if check_password_hash(user.password, password):
                login_user(user)
                flash(f"Welcome {user.username}", category="success")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid password", category="danger")
        
        # return redirect(url_for('dashboard'))
    
    return render_template("login.html", form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password = form.password.data

        user = User(
            email=email, 
            username=username, 
            password=generate_password_hash(password)
        )

        _new_otp = generate_random_otp(5)
        token = OTPToken(
            token=_new_otp,
            expires_at=datetime.now() + timedelta(minutes=OTP_LIFESPAN_MINUTES),
            user=user
        )

        db.session.add_all([user, token])
        db.session.commit()

        msg = Message(
            subject=f"Verify Account: Your OTP is {_new_otp}",
            body=f"Welcome\nYour OTP is {token.token}",
            recipients=[user.email]
        )

        html_text = render_template(
            "email/verify-email.html", 
            username=user.username, 
            otp=token.token
        )

        msg.html = html_text
        # mail.send(msg)
        # send_mail_async(message=msg)
        try:
            brevo_response = send_registration_mail(
                to=user.email,
                username=user.username,
                otp=_new_otp,
                html_content=html_text
            )

            if brevo_response.status_code != 201 or brevo_response.status_code != 200:
                raise Exception

        except Exception as e:
            flash("Account created but there was an error sending the email", category="danger")
            print("An error occured while sending", e)
        else:
            session['user_being_verified'] = user.id

            flash("Sign up success. Please verify your email", category="info")
            return redirect(url_for('verify_otp'))

    return render_template("register.html", form=form)


@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        token = request.form.get('token')

        user_id = session.get('user_being_verified')

        if user_id is None:
            flash("Invalid request", "danger")
            return abort(400)

        user = User.query.get(user_id)
        otp_token = OTPToken.query.filter_by(token=token, user_id=user_id).first()

        if otp_token:
            # if token HAS NOT EXPIRED
            if not otp_token.is_used and  otp_token.expires_at > datetime.now():
                otp_token.user.is_verified = True
                otp_token.is_used = True

                db.session.add(otp_token)
                db.session.commit()

                session.pop("user_being_verified")

                flash("OTP is verified", category="success")
                login_user(user)
                return redirect(url_for('dashboard'))

            flash("Token has been used or expired", category="danger")
            return render_template("verify-otp.html")

        flash("Invalid OTP token", category="danger")

    return render_template("verify-otp.html")


@app.post("/resend-otp")
def resend_otp():

    data = json.loads(request.data)
    email = data.get('email')
    if not email:
        return jsonify({'message': 'Email not provided'}, status=400)

    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"message": "User not found"})

    if user.is_verified:
        return jsonify({"message": "User already verified"})

    # If User exists
    _new_otp = generate_random_otp(5)
    token = OTPToken(
        token=_new_otp,
        expires_at=datetime.now() + timedelta(minutes=OTP_LIFESPAN_MINUTES),
        user=user,
    )

    db.session.add_all([user, token])
    db.session.commit()

    msg = Message(
        subject=f"Verify Account: Your OTP is {_new_otp}",
        body=f"Welcome\nYour OTP is {token.token}",
        recipients=[user.email],
    )

    html_text = render_template(
        "email/verify-email.html", username=user.username, otp=token.token
    )

    msg.html = html_text
    mail.send(msg)
    
    return jsonify({"message": "Resent OTP"})

    # user_id = session.get("user_being_verified")

    # if user_id and (user := User.query.get(user_id)):

    #     _new_otp = generate_random_otp(5)
    #     token = OTPToken(
    #         token=_new_otp,
    #         expires_at=datetime.now() + timedelta(minutes=OTP_LIFESPAN_MINUTES),
    #         user=user,
    #     )

    #     db.session.add_all([user, token])
    #     db.session.commit()

    #     msg = Message(
    #         subject=f"Verify Account: Your OTP is {_new_otp}",
    #         body=f"Welcome\nYour OTP is {token.token}",
    #         recipients=[user.email],
    #     )

    #     html_text = render_template(
    #         "email/verify-email.html", username=user.username, otp=token.token
    #     )

    #     msg.html = html_text
    #     mail.send(msg)
    #     return jsonify({"message": "Resent OTP"})

    # return jsonify({"message": "User not found"})


@app.get('/logout')
@login_required
def logout():
    logout_user()
    flash("Log out success", category="success")
    return redirect(url_for('login'))


@app.route("/new-post", methods=["GET", "POST"])
@login_required
def create_post():
    # obj = Post(title="mY POST TITLE", body="lOREM IPSUM")
    
    form = PostForm()

    if form.validate_on_submit():
        title = form.title.data
        body = form.body.data

        new_post = Post(title=title, body=body, author=current_user)
        db.session.add(new_post)
        db.session.commit()

        flash("Post created successfully", category='success')
        return redirect(url_for('dashboard'))
    
    return render_template("new_post.html", form=form)


@app.get('/posts/<int:id>')
@login_required
def post_detail(id: int):
    post = Post.query.get(id)

    if post is None:
        return abort(404)
    
    if current_user != post.author:
        return abort(403, "Cannot view other user's post")
    
    return render_template("post-detail.html", post=post)


@app.post('/posts/delete/<id>')
@login_required
def delete_post(id):
    post = Post.query.get(id)

    if post:
        db.session.delete(post)
        db.session.commit()
        flash("Deleted post success", category="success")
        return redirect(url_for("dashboard"))
    else:
        flash("Post not found", category="warning")
        return redirect(url_for("dashboard"))


@app.route('/posts/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    edit_form = PostForm()
    post = Post.query.get_or_404(id)

    if post.author != current_user:
        flash("Cannot edit other user's post", category='danger')
        return redirect(url_for("dashboard"))


    if request.method == 'GET':
        edit_form.title.data = post.title
        edit_form.body.data = post.body

    elif edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.body = edit_form.body.data

        db.session.commit()
        flash("Post updated successfully", category="success")
        return redirect(url_for("dashboard"))

    return render_template("edit-post.html", form=edit_form)


if __name__ == '__main__':
    app.run(debug=True)


if __name__ == '__main__':
    app.run(debug=True)
