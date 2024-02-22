from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
import os

# Initialize Flask application
app = Flask(__name__, template_folder='templates')

# Load configuration from environment variables
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///ticketing_system.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.example.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
mail = Mail(app)

# Setup login manager
login_manager.login_view = 'auth.login'

# Blueprint registration (Example)
from app.auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

from app.tickets import tickets as tickets_blueprint
app.register_blueprint(tickets_blueprint, url_prefix='/tickets')

# Ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass
