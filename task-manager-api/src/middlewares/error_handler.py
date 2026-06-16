import logging
from flask import jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Requisição inválida'}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Recurso não encontrado'}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'error': 'Método não permitido'}), 405

    @app.errorhandler(ValueError)
    def validation_error(e):
        return jsonify({'error': str(e)}), 400

    @app.errorhandler(Exception)
    def internal_error(e):
        logger.exception("Erro não tratado")
        return jsonify({'error': 'Erro interno do servidor'}), 500
