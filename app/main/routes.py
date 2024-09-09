"""Main route views"""

from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from forms import BiographyEditForm, CommentForm
from models import Biography,Comment
from datetime import datetime
from flask_login import login_required, current_user
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

@main_bp.route("/submit_comment")
def submit_comment():
    return render_template('biography.html')

@login_required
def biography(biography_id):
    biography = Biography.query.get_or_404(biography_id)
    comments = Comment.query.filter_by(biography_id = biography_id).all()
    if BiographyEditForm().validate_on_submit and current_user.is_manager:
        BiographyEditForm.populate_obj(biography)
        db.session.commit()
        flash('Biography page updated successfully')
    if CommentForm().validate_on_submit():
        new_comment = Commnent(
            user_id=current_user.id,
            text=CommentForm().comment.data,
            timestamp=datetime.now()
        )
        db.session.add(new_comment)
        db.session.commit()
        flash('Comments added successfully')
        return(redirect(url_for('biography')))
    return render_template('biography.html')