import logging
from datetime import datetime, timezone
from flask import Flask
from flask_cors import CORS
from src.config.settings import Config
from src.database import db
from src.routes.task_routes import task_bp
from src.routes.user_routes import user_bp
from src.routes.category_routes import category_bp
from src.routes.report_routes import report_bp
from src.middlewares.error_handler import register_error_handlers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(report_bp)

    register_error_handlers(app)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(datetime.now(timezone.utc))}

    @app.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    with app.app_context():
        db.create_all()

    return app
