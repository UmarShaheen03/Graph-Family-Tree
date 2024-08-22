"""Main route views"""

from flask import Blueprint, render_template, flash, redirect, url_for, request, session

main_bp = Blueprint('main_bp', __name__)

@main_bp.route("/")
def home_page():
    """The landing page"""
    return render_template('home.html')

@main_bp.route("/tree")
def tree_page():
    """The landing page"""
    return render_template('tree.html')

