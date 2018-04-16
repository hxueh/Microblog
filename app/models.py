from datetime import datetime
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from markdown import markdown
from bleach import linkify, clean
from . import db, login_manager

from os import urandom
from base64 import b64encode
from otpauth import OtpAuth


class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    permissions = db.Column(db.Integer)
    # http://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        # https://docs.python.org/3/library/functions.html#super
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    # https://stackoverflow.com/questions/23508248/why-do-we-use-staticmethod
    # https://docs.python.org/3/library/functions.html#staticmethod
    @staticmethod
    def insert_roles():
        roles = {
            # User is 1, 2, 4; Admin is all
            # Using number to represent permissions
            # If we have permisssion to moderate, we will have permission to write.
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
                              Permission.MODERATE, Permission.ADMIN]
        }
        # User, Moderator, Administrator
        # I don't know why but it must the Administrator can't add so I try 2 time
        for r in roles:
            # Check if there is role that needed to be create
            role = Role.query.filter_by(name=r).first()
            if role is None:
                # Create a role
                role = Role(name=r)
            role.reset_permissions()
            # For permissions in role
            for perm in roles[r]:
                role.add_permissions(perm)
            db.session.add(role)
        db.session.commit()

    def add_permissions(self, perm):
        if not self.has_permisssions(perm):
            self.permissions += perm

    def remove_permissions(self, perm):
        if self.has_permisssions(perm):
            self.permissions -= perm

    def has_permisssions(self, perm):
        return self.permissions > perm

    def reset_permissions(self):
        self.permissions = 0

    def __repr__(self):
        return self.name


class Follow(db.Model):
    __tablename__ = 'follow'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    time = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True, unique=True)
    email = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    twofa = db.Column(db.String(64))
    twofa_enable = db.Column(db.Boolean, default=False)
    nickname = db.Column(db.String(64))
    about = db.Column(db.Text)
    location = db.Column(db.String(64))
    register_time = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Key
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    # If we delete the user, delete all the posts
    # http://docs.sqlalchemy.org/en/latest/orm/cascades.html
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')

    # If we delete the user, delete all the comments
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')

    # If A follow B, A is a follower. Thus in the table, A will be marked as follower
    following = db.relationship('Follow',
                                foreign_keys=[Follow.follower_id],
                                backref=db.backref('follower', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    follower = db.relationship('Follow',
                               foreign_keys=[Follow.followed_id],
                               backref=db.backref('followed', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['MAIL_USERNAME']:
                # If the user is the admin, make it admin.
                self.role = Role.query.filter_by(name='Administrator').first()
            else:
                # Or make it regular user
                self.role = Role.query.filter_by(name='User').first()

        self.twofa = b64encode(urandom(16)).decode('utf-8')
        # commit changes to database.
        db.session.commit()

    # Using property so that we can create user using User(password='password')
    @property
    def password(self):
        raise AttributeError('No one can read password.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_email_token(self):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=3600)
        return s.dumps({'confirmed': self.id}).decode('utf-8')

    def verify_email_token(self, token):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=3600)
        try:
            load = s.loads(token.encode('utf-8'))
        except:
            return False
        if load['confirmed'] == self.id:
            self.confirmed = True
            db.session.add(self)
            db.session.commit()
            return True
        else:
            return False

    def generate_password_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=3600)
        return s.dumps({'password_reset': self.id}).decode('utf-8')

    @staticmethod
    def verity_password_reset_token(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=3600)
        try:
            load = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(load['password_reset'])
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        db.session.commit()
        return True

    def generate_email_changing_token(self, new_email):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=3600)
        return s.dumps({'email_changing': self.id, 'new_email': new_email}).decode('utf-8')

    @staticmethod
    def verify_email_changing_token(token):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=3600)
        try:
            load = s.loads(token.encode('utf-8'))
        except:
            return False
        # Get who is changing email address.
        user = User.query.get(load['email_changing'])
        if user is None:
            return False
        user.email = load['new_email']
        db.session.add(user)
        db.session.commit()
        return True

    def can(self, perm):
        return self.role.has_permisssions(perm)

    def is_admin(self):
        return self.can(Permission.ADMIN)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def follow(self, to_follow):
        if not self.is_following(to_follow):
            follow = Follow(follower=self, followed=to_follow)
            db.session.add(follow)
            db.session.commit()

    def unfollow(self, to_unfollow):
        if self.is_following(to_unfollow):
            unfollow = Follow.query.filter_by(follower_id=self.id, followed_id=to_unfollow.id).first()
            db.session.delete(unfollow)
            db.session.commit()

    def is_following(self, user):
        follow = Follow.query.filter_by(follower_id=self.id, followed_id=user.id).first()
        if follow is None:
            return False
        else:
            return True

    def is_followed_by(self, user):
        follow = Follow.query.filter_by(follower_id=user.id, followed_id=self.id).first()
        if follow is None:
            return False
        else:
            return True

    def create_twofa(self):
        return OtpAuth(self.twofa).to_uri(type='totp', label=self.id, issuer='microblog')

    def verify_twofa(self, token):
        return OtpAuth(self.twofa).valid_totp(token)

    def disable_twofa(self):
        self.twofa = b64encode(urandom(16)).decode('utf-8')
        self.twofa_enable = False
        db.session.add(self)
        db.session.commit()

    def delete_user(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return self.nickname or self.username


class AnomymousUser(AnonymousUserMixin):
    @staticmethod
    def can(permission):
        return False

    @staticmethod
    def is_admin():
        return False


login_manager.anonymous_user = AnomymousUser


# https://flask-login.readthedocs.io/en/latest/#how-it-works
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body = db.Column(db.Text)
    # User's input is markdown, convert them to HTML
    body_html = db.Column(db.Text)
    time = db.Column(db.DateTime, default=datetime.utcnow)
    repost = db.Column(db.Boolean, default=False)
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    def delete_post(self):
        db.session.delete(self)
        db.session.commit()


# http://docs.sqlalchemy.org/en/latest/orm/events.html#sqlalchemy.orm.events.AttributeEvents.set
@db.event.listens_for(Post.body, 'set')
def convert_md_to_html(target, value, oldvalue, initiator):
    target.body_html = linkify(clean(markdown(value), strip=True))


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    time = db.Column(db.DateTime, default=datetime.utcnow)

    def delete_comment(self):
        db.session.delete(self)
        db.session.commit()


@db.event.listens_for(Comment.body, 'set')
def convert_md_to_html(target, value, oldvalue, initiator):
    target.body_html = linkify(clean(markdown(value), strip=True))
