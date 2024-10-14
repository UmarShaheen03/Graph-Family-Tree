"""Flask app configurations"""

import os
basedir = os.path.abspath(os.path.dirname(__file__))
WEBSITE_URL = "http://127.0.0.1:5000/" #TODO change when deploying

NEO4J_URI='neo4j+ssc://633149e1.databases.neo4j.io' #TODO encrypt?
NEO4J_USERNAME='neo4j'
NEO4J_PASSWORD='1b_L2Kp4ziyuxubevqHTgHDGxZ1VjYXROCFF2USqdNE'

class Config:
    """General base config class"""
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'

    #Cryptographic key for signature/tokens to defend web forms against CSRF
    SECRET_KEY = "test1234"
    # SECRET_KEY = os.environ.get('SECRET_KEY')

    SQLALCHEMY_DATABASE_URI = 'postgresql://u4kb3n540fetg:p3f5bb2d853c215b59a7048c59029b84c74df6eaedc7637a3581b03f38ced6076@cbec45869p4jbu.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d6s73p5t0q3ev9'
    
    WTF_CSRF_ENABLED = False

    SERVER_NAME = "127.0.0.1:5000" #TODO CHANGE WHEN DEPLOYING!!!

