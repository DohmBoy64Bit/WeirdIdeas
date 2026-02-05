from flask import Flask
import os
from config import Config
from extensions import db, login_manager, migrate
from backend.models import user, content

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register Blueprints
    from backend.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from backend.routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Deadit backend is running'}

    # Initialize Automation Scheduler
    from backend.scheduler import init_scheduler
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        # Only start scheduler in production or in the reloader's main process
        # to prevent double-execution during dev restart.
        init_scheduler(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
