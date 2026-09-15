from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)

    from app import models  # noqa: F401

    from app.services.auth_service import get_current_user, generate_csrf_token
    app.jinja_env.globals['get_current_user'] = get_current_user
    app.jinja_env.globals['csrf_token'] = generate_csrf_token

    from app.routes.main import bp as main_bp
    from app.routes.universe import bp as universe_bp
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(universe_bp)
    app.register_blueprint(auth_bp)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500

    return app
