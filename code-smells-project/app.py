from flask import Flask, jsonify
from flask_cors import CORS
from src.config.settings import Config
from src.models.database import init_app, init_schema
from src.routes.produto_routes import produto_bp
from src.routes.usuario_routes import usuario_bp
from src.routes.pedido_routes import pedido_bp
from src.routes.system_routes import system_bp
from src.routes.admin_routes import admin_bp
from src.middlewares.error_handler import register_error_handlers


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    init_app(app)

    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(admin_bp)

    register_error_handlers(app)

    @app.route("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health"
            }
        })

    return app


if __name__ == "__main__":
    init_schema()
    app = create_app()

    print("=" * 50)
    print("SERVIDOR INICIADO")
    print("Rodando em http://localhost:5000")
    print("=" * 50)

    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
