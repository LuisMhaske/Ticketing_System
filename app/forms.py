from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('New Password', validators= [DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo(
        'password', message='Passwords must match')])
    submit = SubmitField('Sign Up')


class CommentForm(FlaskForm):
    comment = StringField('Add your comments/query here', validators=[DataRequired(
        message="Please enter a comment before submitting.")])
    submit = SubmitField('Submit Comment')


class TicketForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Submit')
