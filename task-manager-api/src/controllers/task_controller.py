import logging
from datetime import datetime
from flask import request, jsonify
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from src.database import db
from src.models.task import Task, _utcnow
from src.models.user import User
from src.models.category import Category
from src.utils.helpers import VALID_STATUSES, MIN_TITLE_LENGTH, MAX_TITLE_LENGTH, parse_date

logger = logging.getLogger(__name__)


class TaskController:
    @staticmethod
    def get_all():
        tasks = Task.query.options(
            joinedload(Task.user),
            joinedload(Task.category),
        ).all()
        result = []
        for t in tasks:
            data = t.to_dict()
            data['overdue'] = t.is_overdue()
            data['user_name'] = t.user.name if t.user else None
            data['category_name'] = t.category.name if t.category else None
            result.append(data)
        return jsonify(result), 200

    @staticmethod
    def get_one(task_id):
        task = db.session.get(Task, task_id)
        if not task:
            return jsonify({'error': 'Task não encontrada'}), 404
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        return jsonify(data), 200

    @staticmethod
    def create():
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400

        title = (data.get('title') or '').strip()
        if not title:
            return jsonify({'error': 'Título é obrigatório'}), 400
        if len(title) < MIN_TITLE_LENGTH:
            return jsonify({'error': 'Título muito curto'}), 400
        if len(title) > MAX_TITLE_LENGTH:
            return jsonify({'error': 'Título muito longo'}), 400

        status = data.get('status', 'pending')
        if status not in VALID_STATUSES:
            return jsonify({'error': 'Status inválido'}), 400

        priority = data.get('priority', 3)
        if not isinstance(priority, int) or priority < 1 or priority > 5:
            return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400

        user_id = data.get('user_id')
        if user_id and not db.session.get(User, user_id):
            return jsonify({'error': 'Usuário não encontrado'}), 404

        category_id = data.get('category_id')
        if category_id and not db.session.get(Category, category_id):
            return jsonify({'error': 'Categoria não encontrada'}), 404

        task = Task(
            title=title,
            description=data.get('description', ''),
            status=status,
            priority=priority,
            user_id=user_id,
            category_id=category_id,
        )

        due_date_str = data.get('due_date')
        if due_date_str:
            parsed = parse_date(due_date_str)
            if not parsed:
                return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
            task.due_date = parsed

        tags = data.get('tags')
        if tags:
            task.tags = ','.join(tags) if isinstance(tags, list) else tags

        try:
            db.session.add(task)
            db.session.commit()
            logger.info("Task criada: %s - %s", task.id, task.title)
            return jsonify(task.to_dict()), 201
        except Exception:
            db.session.rollback()
            logger.exception("Erro ao criar task")
            return jsonify({'error': 'Erro ao criar task'}), 500

    @staticmethod
    def update(task_id):
        task = db.session.get(Task, task_id)
        if not task:
            return jsonify({'error': 'Task não encontrada'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400

        if 'title' in data:
            title = (data['title'] or '').strip()
            if len(title) < MIN_TITLE_LENGTH:
                return jsonify({'error': 'Título muito curto'}), 400
            if len(title) > MAX_TITLE_LENGTH:
                return jsonify({'error': 'Título muito longo'}), 400
            task.title = title

        if 'description' in data:
            task.description = data['description']

        if 'status' in data:
            if data['status'] not in VALID_STATUSES:
                return jsonify({'error': 'Status inválido'}), 400
            task.status = data['status']

        if 'priority' in data:
            p = data['priority']
            if not isinstance(p, int) or p < 1 or p > 5:
                return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400
            task.priority = p

        if 'user_id' in data:
            if data['user_id'] and not db.session.get(User, data['user_id']):
                return jsonify({'error': 'Usuário não encontrado'}), 404
            task.user_id = data['user_id']

        if 'category_id' in data:
            if data['category_id'] and not db.session.get(Category, data['category_id']):
                return jsonify({'error': 'Categoria não encontrada'}), 404
            task.category_id = data['category_id']

        if 'due_date' in data:
            if data['due_date']:
                parsed = parse_date(data['due_date'])
                if not parsed:
                    return jsonify({'error': 'Formato de data inválido'}), 400
                task.due_date = parsed
            else:
                task.due_date = None

        if 'tags' in data:
            tags = data['tags']
            task.tags = ','.join(tags) if isinstance(tags, list) else tags

        task.updated_at = _utcnow()

        try:
            db.session.commit()
            logger.info("Task atualizada: %s", task.id)
            return jsonify(task.to_dict()), 200
        except Exception:
            db.session.rollback()
            logger.exception("Erro ao atualizar task")
            return jsonify({'error': 'Erro ao atualizar'}), 500

    @staticmethod
    def delete(task_id):
        task = db.session.get(Task, task_id)
        if not task:
            return jsonify({'error': 'Task não encontrada'}), 404
        try:
            db.session.delete(task)
            db.session.commit()
            logger.info("Task deletada: %s", task_id)
            return jsonify({'message': 'Task deletada com sucesso'}), 200
        except Exception:
            db.session.rollback()
            logger.exception("Erro ao deletar task")
            return jsonify({'error': 'Erro ao deletar'}), 500

    @staticmethod
    def search():
        q = request.args.get('q', '')
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        user_id = request.args.get('user_id', '')

        query = Task.query
        if q:
            query = query.filter(
                db.or_(Task.title.like(f'%{q}%'), Task.description.like(f'%{q}%'))
            )
        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == int(priority))
        if user_id:
            query = query.filter(Task.user_id == int(user_id))

        return jsonify([t.to_dict() for t in query.all()]), 200

    @staticmethod
    def stats():
        total = Task.query.count()
        status_counts = dict(
            db.session.query(Task.status, func.count(Task.id))
            .group_by(Task.status)
            .all()
        )
        overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())
        done = status_counts.get('done', 0)

        return jsonify({
            'total': total,
            'pending': status_counts.get('pending', 0),
            'in_progress': status_counts.get('in_progress', 0),
            'done': done,
            'cancelled': status_counts.get('cancelled', 0),
            'overdue': overdue_count,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        }), 200
