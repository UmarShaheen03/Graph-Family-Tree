from accounts import *
from unittest import TestCase
from config import TestConfig
from app import create_app, db

class AccountTests(TestCase):
    def setUp(self):
        test_app = create_app(TestConfig)
        self.app_context = test_app.app_context
        self.app_context.push()
        db.create_all()
        self.init_test_db()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def init_test_db():
        test_admin = User(
            user_id=0,
            username="Test Admin",
            email="cooptrooper04@gmail.com", #using my personal email for testing
            admin=True,
            password_hash=str(generate_password_hash("test1234"))
        )

        test_user = User(
            user_id=1,
            username="Test User",
            email="cooptrooper04@gmail.com", #using my personal email for testing
            admin=False,
            password_hash=str(generate_password_hash("test1234"))
        )

    def signup_test():
        pass

    def login_tests():
        pass

    def forgot_tests():
        pass

    def reset_tests():
        pass
