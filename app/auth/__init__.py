from flask import Blueprint

# http://flask.pocoo.org/docs/0.12/blueprints/#my-first-blueprint
auth = Blueprint('auth', __name__)

from . import views