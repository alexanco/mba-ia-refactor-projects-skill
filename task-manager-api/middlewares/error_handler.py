from flask import jsonify


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': str(e), 'success': False}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Recurso não encontrado', 'success': False}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'error': 'Método não permitido', 'success': False}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'error': 'Erro interno do servidor', 'success': False}), 500
