from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    TextAreaField
)
from wtforms.validators import DataRequired, Length, Email, ValidationError
from flask_login import current_user
from models import User


# ---------------- REGISTER ----------------

class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=4, max=20)]
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8)]
    )
    submit = SubmitField("Register")


# ---------------- LOGIN ----------------

class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


# ---------------- UPDATE ACCOUNT ----------------

class UpdateAccountForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=4, max=20)]
    )

    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    picture = FileField(
        "Update Profile Picture",
        validators=[FileAllowed(["jpg", "png", "jpeg"])]
    )

    submit = SubmitField("Update")

    def validate_username(self, username):
        if current_user.is_authenticated and username.data != current_user.username:
            existing_username = User.query.filter_by(
                username=username.data
            ).first()

            if existing_username:
                raise ValidationError(
                    "Username already exists. Please choose another."
                )

    def validate_email(self, email):
        if current_user.is_authenticated and email.data != current_user.email:
            existing_email = User.query.filter_by(
                email=email.data
            ).first()

            if existing_email:
                raise ValidationError(
                    "Email already registered. Please log in."
                )


# ---------------- POST FORM (FIXED) ----------------

class PostForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[DataRequired(), Length(min=1, max=100)]
    )

    content = TextAreaField(
        "Content",
        validators=[DataRequired()]
    )

    submit = SubmitField("Post")