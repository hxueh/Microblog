import os

# __file__ means this file, that is config.py
# dirname will show the path of __file__, that is microblog
basedir = os.path.abspath(os.path.dirname(__file__))

Mail_Provider = 'Google'

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ThisIsAHardKey'

    MAIL_SERVER = os.environ.get(Mail_Provider + 'MAIL_SERVER')
    MAIL_PORT = int(os.environ.get(Mail_Provider + 'MAIL_PORT')) or 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get(Mail_Provider + 'MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get(Mail_Provider + 'MAIL_PASSWORD')
    MAIL_SUBJECT_PREFIX = '[MICROBLOG]'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    POSTS_PER_PAGE = 50
    FOLLOW_PER_PAGE = 2
    COMMENTS_PER_PAGE = 20

    @staticmethod
    def init_app(app):
        pass

    
class SQLConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')


config = {
    'default': SQLConfig
}