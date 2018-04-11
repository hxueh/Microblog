from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_pagedown import PageDown
from flask_bcrypt import Bcrypt
from flask_qrcode import QRcode
from config import config


bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
pagedown = PageDown()
bcrypt = Bcrypt()
login_manager = LoginManager()
qrcode = QRcode()
login_manager.login_view = 'auth.login'

# https://stackoverflow.com/questions/40326651/flask-mail-sending-email-asynchronously-based-on-flask-cookiecutter

def create_app(config_name):
    
    # From application.py, set config_name
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    pagedown.init_app(app)
    bcrypt.init_app(app)
    qrcode.init_app(app)
    login_manager.init_app(app)

    #http://flask.pocoo.org/docs/0.12/blueprints/#registering-blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app