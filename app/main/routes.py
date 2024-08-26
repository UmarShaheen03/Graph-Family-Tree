"""Main route views"""

from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from app.forms import AddNodeForm
main_bp = Blueprint('main_bp', __name__)

@main_bp.route("/")
def home_page():
    """The landing page"""
    return render_template('home.html')

@main_bp.route("/login")
def login_page():
    """The login page"""
    return render_template('login.html')

@main_bp.route("/tree")
def tree_page():
    """A family tree page"""
    return render_template('tree.html')

@main_bp.route("/biography")
def biography_page():
    """The biography page"""
    return render_template('biography.html')

@main_bp.route("/addnode", methods=['GET', 'POST'])
def addnode_page():
    """The Add node page"""
    form = AddNodeForm()
    
    return render_template('addnode.html', form=form)