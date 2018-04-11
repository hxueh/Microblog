from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo

from ..models import User


class LoginForm(FlaskForm):
    user = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(6, 128)])
    token = StringField('Two Factor Authentication Token, leave it blank if not setup.')
    remember = BooleanField('Keep Logging In', default=True)
    submit = SubmitField('Submit')


class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 32)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(6, 128)])
    repeat = PasswordField('Repeat Password', validators=[DataRequired(), Length(6, 128), EqualTo('password')])
    submit = SubmitField('Submit')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired(), Length(6, 128)])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(6, 128)])
    repeat_new_password = PasswordField('New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Submit')


class ChangeEmailForm(FlaskForm):
    email = StringField('New Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Submit')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Submit')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(6, 128)])
    repeat_password = PasswordField('Repet New Password', validators=[DataRequired(), Length(6, 128), EqualTo('password')])
    submit = SubmitField('Submit')


class TwoFactorAuthenticatorForm(FlaskForm):
    token = StringField('Token', validators=[DataRequired(), Length(6, 6)])
    submit = SubmitField('Submit')


class DeleteUserForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('DELETE')