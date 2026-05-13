from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    is_verified = db.Column(db.Boolean, nullable=True, default=False)
    password = db.Column(db.String(255), nullable=False)
    
    posts = db.relationship('Post', back_populates="author")
    tokens = db.relationship('OTPToken', back_populates='user')

    def __str__(self):
        return f"<User: {self.email}>"


class Post(db.Model):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="posts")


class OTPToken(db.Model):
    __tablename__ = "tokens"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(5))
    is_expired = db.Column(db.Boolean, default=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(), default=datetime.now())
    expires_at = db.Column(db.DateTime())

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", back_populates='tokens')

