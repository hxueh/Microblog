import os

from flask_migrate import Migrate, upgrade
from app import create_app, db
from app.email import sendmail
from app.models import User, Follow, Role, Permission, Post, Comment

app = create_app('default')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Follow=Follow, Role=Role,
                Permission=Permission, Post=Post, Comment=Comment, sendmail=sendmail)

@app.cli.command()
def deploy():
    upgrade()
    Role.insert_roles()