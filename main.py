"""Entry point for the flask application"""

from app import create_app

flask_app = create_app("Config")
if __name__ == "__main__":
    flask_app.run(debug=False)
