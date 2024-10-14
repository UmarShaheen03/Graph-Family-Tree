"""Blueprint for the main parts of the app"""

from flask import Blueprint

main_bp = Blueprint('main_bp', __name__)

from . import routes