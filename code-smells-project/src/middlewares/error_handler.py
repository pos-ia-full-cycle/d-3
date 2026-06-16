import logging
from flask import jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"erro": "Recurso não encontrado", "sucesso": False}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"erro": "Método não permitido", "sucesso": False}), 405

    @app.errorhandler(ValueError)
    def validation_error(e):
        return jsonify({"erro": str(e), "sucesso": False}), 400

    @app.errorhandler(Exception)
    def internal_error(e):
        logger.exception("Erro interno não tratado")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
