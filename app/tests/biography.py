import unittest
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import os
from flask import url_for, app, Blueprint
from app.models import Comment, Notification
import io
from PIL import Image
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
import sys

main_bp = Blueprint('main_bp', __name__)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
def create_test_image():
    """Creates an in-memory test image"""
    image = Image.new('RGB', (100, 100), color = 'red') 
    img_io = io.BytesIO()
    image.save(img_io, 'JPEG') 
    img_io.seek(0)  
    img_io.name = 'test_image.jpg' 
    return img_io
class BiographyPageTest(unittest.TestCase):
    
    def setUp(self):
        self.client = self.app.test_client()
        self.upload_path = "static/uploads"

    def login(self, username, password):
        return self.client.post(url_for('main_bp.login_request'), data={
            'username': username,
            'password': password
        }, follow_redirects=True)
    
    def logout(self):
        return self.client.get(url_for('main_bp.logout_request'), follow_redirects=True)

    def test_image_upload(self):
        self.login('user_test', 'test1234')
        image_data = create_test_image()
        response = self.client.post(
            url_for('main_bp.biography', name='Linda_Barnes'),
            data={
                'profile_image': (image_data, image_data.name)
            },
            content_type='multipart/form-data',
            follow_redirects=True
        )
        assert b'Image uploaded successfully.' in response.data
        uploaded_file_path = os.path.join(self.upload_path, 'test_image.jpg')
        assert os.path.exists(uploaded_file_path)

    def test_submit_comment(self):
        self.login('user_test', 'test1234')
        response = self.client.post(url_for('main_bp.biography', name='Linda_Barnes'), data={
            'comment': 'This is a test comment.'
        }, follow_redirects=True)
        assert b'Comment added successfully' in response.data
        comment = Comment.query.filter_by(bio_name='Linda_Barnes').first()
        assert comment is not None
        assert comment.text == 'This is a test comment.'
        assert comment.username == 'user_test'

    def test_notification_comment(self):
        self.login('user_test', 'test1234')
        assert response.status_code == 200
        response = self.client.post(url_for('main_bp.biography', name='Linda_Barnes'), data={
        'comment': 'This is a test comment.'
    }, follow_redirects=True)
        assert b'Comment added successfully' in response.data
        self.logout()  

        response = self.client.post(url_for('main_bp.login_request'), data={
        'username': 'admin_test',
        'password': 'test1234'
    }, follow_redirects=True)
        assert response.status_code == 200
        notifications = Notification.query.filter_by(user_id=4).all()  # Assuming admin_test has user_id=4
        assert len(notifications) > 0
        assert 'commented on Person Linda_Barnes' in notifications[0].message

    def test_admin_edit_biography(self):
        self.login('admin_test', 'test1234')
        response = self.client.get(url_for('main_bp.biography', name='Linda_Barnes'))
        assert b'Edit Bio' in response.data
        response = self.client.get(url_for('main_bp.edit_biography', person_name='Linda_Barnes'))
        assert response.status_code == 200 

    def test_user_edit_biography(self):
        self.login('user_test', 'test1234')
        response = self.client.get(url_for('main_bp.biography', name='Linda_Barnes'))
        assert b'Edit Bio' not in response.data
        response = self.client.get(url_for('main_bp.edit_biography', person_name='Linda_Barnes'))
        assert response.status_code == 403
        self.logout() 
    

if __name__ == "__main__":
    unittest.main()