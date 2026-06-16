import logging
from flask import jsonify
from src.database import db
from src.models.user import User
from src.services.report_service import ReportService

logger = logging.getLogger(__name__)


class ReportController:
    @staticmethod
    def summary():
        report = ReportService.summary()
        return jsonify(report), 200

    @staticmethod
    def user_report(user_id):
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        report = ReportService.user_report(user_id)
        report['user'] = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        }
        return jsonify(report), 200
