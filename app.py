import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable CORS for frontend requests
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    
    # Configure JWT
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "unfv-jwt-super-secret-key-9988")
    app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
    app.config["JWT_COOKIE_SECURE"] = False # Set to True in production with HTTPS
    app.config["JWT_REFRESH_COOKIE_NAME"] = "refresh_token"
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False # Simplified for Hackathon MVP demo
    
    jwt = JWTManager(app)
    
    # Initialize DB
    db.init_app(app)
    
    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.academic import academic_bp
    from blueprints.timeline import timeline_bp
    from blueprints.evaluator import evaluator_bp
    from blueprints.resources import resources_bp
    from blueprints.wellbeing import wellbeing_bp
    from blueprints.admin import admin_bp
    from blueprints.events import events_bp
    from blueprints.copilot import copilot_bp
    from blueprints.study_routes import study_routes_bp
    from blueprints.crowdsourcing import crowdsourcing_bp
    from blueprints.cells import cells_bp
    from blueprints.docente_analytics import docente_analytics_bp
    from blueprints.notas import notas_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(academic_bp, url_prefix='/api/academic')
    app.register_blueprint(timeline_bp, url_prefix='/api/timeline')
    app.register_blueprint(evaluator_bp, url_prefix='/api/evaluator')
    app.register_blueprint(resources_bp, url_prefix='/api/resources')
    app.register_blueprint(wellbeing_bp, url_prefix='/api/wellbeing')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(events_bp, url_prefix='/api/events')
    app.register_blueprint(copilot_bp, url_prefix='/api/copilot')
    app.register_blueprint(study_routes_bp, url_prefix='/api/study-routes')
    app.register_blueprint(crowdsourcing_bp, url_prefix='/api/crowdsourcing')
    app.register_blueprint(cells_bp, url_prefix='/api/cells')
    app.register_blueprint(docente_analytics_bp, url_prefix='/api/docente')
    app.register_blueprint(notas_bp, url_prefix='/api/notas')
    
    @app.route('/')
    def index():
        return jsonify({
            "sistema": "Tutor Inteligente Adaptativo UNFV",
            "version": "1.1.0-MVP",
            "estado": "Operativo",
            "módulos": ["RBAC", "Academic", "Timeline", "Evaluator", "Resources", "Wellbeing"]
        })
        
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Recurso no encontrado"}), 404
        
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({"error": "Error interno del servidor"}), 500

    # Ensure tables exist
    with app.app_context():
        db.create_all()
        pass
        
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
