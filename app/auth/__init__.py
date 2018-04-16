from flask import Blueprint

from . import views

# http://flask.pocoo.org/docs/0.12/blueprints/#my-first-blueprint
auth = Blueprint('auth', __name__)
