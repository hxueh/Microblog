from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Email
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField
from ..models import Role, User


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 32)])
    nickname = StringField('Nickname', validators=[Length(max=64)])
    about = TextAreaField('About Me')
    location = StringField('Location', validators=[Length(max=64)])
    submit = SubmitField('Submit')


class AdminEditProfileForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(1, 64)])
    username = StringField('Username', validators=[DataRequired(), Length(1, 32)])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    nickname = StringField('Nickname', validators=[Length(max=64)])
    location = StringField('Location', validators=[Length(max=64)])
    about = TextAreaField('About Me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(AdminEditProfileForm, self).__init__(*args, **kwargs)
        # Set role choices
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class PostForm(FlaskForm):
    body = PageDownField("What's on your mind?", validators=[DataRequired()])
    submit = SubmitField('Submit')


class CommentForm(FlaskForm):
    body = StringField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit')