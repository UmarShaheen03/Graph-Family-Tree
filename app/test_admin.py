import pytest
from flask import Flask, session              # Import the Flask app instance named 'flask_app'
from app.main import routes     # Import the serializer from app/main/routes.py
from app import create_app   # Import the create_app function to generate the Flask app

@pytest.fixture
def client():
    # Create the Flask app instance for testing
    flask_app = create_app()
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test_secret_key'

    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client

# Test for successful admin privilege request
def test_request_admin_success(client):
    # Set up session for testing
    with client.session_transaction() as sess:
        sess['user_email'] = 'testuser@example.com'
        sess['username'] = 'testuser'  # Add username to the session as well

    # Make the POST request to the /request_admin route
    response = client.post('/request_admin')

    assert response.status_code == 200

    # Check that the message returned is correct
    json_data = response.get_json()
    assert json_data['message'] == sess['user_email']

# Test for failure when no email is in the session
def test_request_admin_no_email(client):
    # Do not set any session variables

    # Make the POST request to the /request_admin route
    response = client.post('/request_admin')

    # Check that the app handles the missing email properly, e.g., returns a 400 or 403 status code
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['error'] == 'User email not found in session'
