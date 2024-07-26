from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import time
from sqlalchemy.exc import OperationalError
import os
from datetime import timedelta
from flask_session import Session

# Add this line to get the DELETE_DB_ON_STARTUP environment variable
DELETE_DB_ON_STARTUP = os.environ.get('DELETE_DB_ON_STARTUP', 'false').lower() == 'true'

app = Flask(__name__, template_folder=os.path.abspath('templates'), static_folder=os.path.abspath('static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['SESSION_FILE_DIR'] = os.path.join(app.root_path, 'flask_session')
app.config['SESSION_USE_SIGNER'] = True
Session(app)

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

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

# Function to delete all tables
def delete_all_tables():
    with app.app_context():
        db.reflect()
        db.drop_all()
        print("All database tables dropped.")

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Import routes and models after app is initialized to avoid circular imports
from routes import *
from models import *

def connect_to_database(retries=5, delay=5):
    for attempt in range(retries):
        try:
            with app.app_context():
                if DELETE_DB_ON_STARTUP:
                    delete_all_tables()
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
    with app.app_context():
        db.create_all()
        if not os.path.exists('migrations'):
            os.system('flask db init')
        os.system('flask db migrate')
        os.system('flask db upgrade')
        
        # Verify that the 'temperature' column exists
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        columns = inspector.get_columns('role')
        if 'temperature' not in [col['name'] for col in columns]:
            print("Warning: 'temperature' column is still missing from 'role' table!")
            print("Attempting to add 'temperature' column manually...")
            with db.engine.connect() as connection:
                connection.execute(text("ALTER TABLE role ADD COLUMN IF NOT EXISTS temperature FLOAT DEFAULT 0.7 NOT NULL"))
                connection.execute(text("UPDATE role SET temperature = 0.7 WHERE temperature IS NULL"))
            print("Manual addition of 'temperature' column completed.")
        else:
            print("'temperature' column exists in 'role' table.")
    
    # Ensure all models are up-to-date with the database schema
    with app.app_context():
        db.create_all()
    
    app.run(host='0.0.0.0', port=5000)
