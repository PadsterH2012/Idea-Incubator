from flask import Flask
from flask_migrate import Migrate
import time
from sqlalchemy.exc import OperationalError
import os
from datetime import timedelta
from flask_session import Session
import logging
from logging.handlers import RotatingFileHandler
from database import db
from sqlalchemy import event, select, exc

def create_app():
    app = Flask(__name__, template_folder=os.path.abspath('templates'), static_folder=os.path.abspath('static'))

    # Set up logging
    if not app.debug:
        file_handler = RotatingFileHandler('error.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Idea Incubator startup')

    # Configure session
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
    app.config['SESSION_FILE_DIR'] = os.path.join(app.root_path, 'flask_session')
    app.config['SESSION_USE_SIGNER'] = True
    Session(app)

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://user:password@db:5432/idea_incubator')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_pre_ping': True,
    }

    # Initialize database
    db.init_app(app)
    
    # Initialize migrations
    migrate = Migrate(app, db)

    # Register routes
    from routes import register_routes
    register_routes(app)

    # Set up database connection event listener
    @event.listens_for(db.engine, "engine_connect")
    def ping_connection(connection, branch):
        if branch:
            return

        try:
            connection.scalar(select(1))
        except exc.DBAPIError as err:
            if err.connection_invalidated:
                connection.scalar(select(1))
            else:
                raise

    # Add request handlers for database session management
    @app.before_request
    def before_request():
        if not hasattr(db.session, 'autocommit'):
            db.session.begin()

    @app.teardown_request
    def teardown_request(exception=None):
        if exception:
            db.session.rollback()
        db.session.remove()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    return app

def connect_to_database(app, retries=5, delay=5):
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
    app = create_app()
    with app.app_context():
        connect_to_database(app)
    app.run(host='0.0.0.0', port=5000)