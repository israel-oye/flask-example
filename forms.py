from flask_wtf import FlaskForm
from wtforms import (
    EmailField,
    PasswordField,
    StringField,
    TextAreaField,
    ValidationError,
)
from wtforms.validators import InputRequired, Length

from models import User


class LoginForm(FlaskForm):
    email = EmailField(
        "Email",
        validators=[
            InputRequired(),
        ],
        render_kw={"class_": "form-control"},
    )
    password = PasswordField("Password", validators=[InputRequired(), Length(min=6)])


class RegisterForm(FlaskForm):
    email = EmailField(
        "Email",
        validators=[
            InputRequired(),
        ],
        render_kw={"class_": "form-control"},
    )
    username = StringField(
        "Username",
        validators=[
            InputRequired(),
        ],
        render_kw={"class_": "form-control"},
    )
    password = PasswordField("Password", validators=[InputRequired(), Length(min=6)])

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Email is not available")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Username is not available")
        

class PostForm(FlaskForm):
    title = StringField("Title", validators=[InputRequired()])
    body = TextAreaField("Body")