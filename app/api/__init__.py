from flask import Blueprint

api = Blueprint('api', __name__)

from . import feeds, questions, notifications
