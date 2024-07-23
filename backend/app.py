from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import time
from sqlalchemy.exc import OperationalError
import os

app = Flask(__name__, template_folder=os.path.abspath('templates'), static_folder=os.path.abspath('static'))
app.secret_key = 'your_secret_key'

# Use the DATABASE_URL environment variable
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://user:password@db:5432/idea_incubator')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_pre_ping': True,
}

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import routes after app is initialized to avoid circular imports
from routes import *

def connect_to_database(retries=5, delay=5):
    for attempt in range(retries):
        try:
            with app.app_context():
                db.create_all()
            print("Successfully connected to the database!")
            return
        except OperationalError as e:
            if attempt < retries - 1:
                print(f"Database connection attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Failed to connect to the database after multiple attempts.")
                raise e

if __name__ == '__main__':
    connect_to_database()
    app.run(host='0.0.0.0', port=5000)
