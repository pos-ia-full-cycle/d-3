import logging
from flask import request, jsonify
from src.database import db
from src.models.category import Category
from src.models.task import Task
from src.utils.helpers import is_valid_color, DEFAULT_COLOR

logger = logging.getLogger(__name__)


class CategoryController:
    @staticmethod
    def get_all():
        from sqlalchemy import func
        task_counts = dict(
            db.session.query(Task.category_id, func.count(Task.id))
            .filter(Task.category_id.isnot(None))
            .group_by(Task.category_id)
            .all()
        )
        result = []
        for c in Category.query.all():
            data = c.to_dict()
            data['task_count'] = task_counts.get(c.id, 0)
            result.append(data)
        return jsonify(result), 200

    @staticmethod
    def create():
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400

        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400

        color = data.get('color', DEFAULT_COLOR)
        if not is_valid_color(color):
            return jsonify({'error': 'Cor inválida. Use formato #RRGGBB'}), 400

        category = Category(
            name=name,
            description=data.get('description', ''),
            color=color,
        )
        try:
            db.session.add(category)
            db.session.commit()
            return jsonify(category.to_dict()), 201
        except Exception:
            db.session.rollback()
            logger.exception("Erro ao criar categoria")
            return jsonify({'error': 'Erro ao criar categoria'}), 500

    @staticmethod
    def update(cat_id):
        cat = db.session.get(Category, cat_id)
        if not cat:
            return jsonify({'error': 'Categoria não encontrada'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400

        if 'name' in data:
            cat.name = (data['name'] or '').strip()
        if 'description' in data:
            cat.description = data['description']
        if 'color' in data:
            if not is_valid_color(data['color']):
                return jsonify({'error': 'Cor inválida. Use formato #RRGGBB'}), 400
            cat.color = data['color']

        try:
            db.session.commit()
            return jsonify(cat.to_dict()), 200
        except Exception:
            db.session.rollback()
            logger.exception("Erro ao atualizar categoria")
            return jsonify({'error': 'Erro ao atualizar'}), 500

    @staticmethod
    def delete(cat_id):
        cat = db.session.get(Category, cat_id)
        if not cat:
            return jsonify({'error': 'Categoria não encontrada'}), 404
        try:
            Task.query.filter_by(category_id=cat_id).update({'category_id': None})
            db.session.delete(cat)
            db.session.commit()
            return jsonify({'message': 'Categoria deletada'}), 200
        except Exception:
            db.session.rollback()
            logger.exception("Erro ao deletar categoria")
            return jsonify({'error': 'Erro ao deletar'}), 500
