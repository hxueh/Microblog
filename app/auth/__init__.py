from flask import Blueprint
auth = Blueprint('auth', __name__)
from . import views

# http://flask.pocoo.org/docs/0.12/blueprints/#my-first-blueprint
