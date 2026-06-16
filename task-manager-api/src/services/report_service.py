import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, case
from src.database import db
from src.models.task import Task, _utcnow
from src.models.user import User
from src.models.category import Category
from src.utils.helpers import calculate_percentage

logger = logging.getLogger(__name__)


class ReportService:
    @staticmethod
    def summary():
        now = _utcnow()
        seven_days_ago = now - timedelta(days=7)

        total_tasks = Task.query.count()
        total_users = User.query.count()
        total_categories = Category.query.count()

        status_counts = dict(
            db.session.query(Task.status, func.count(Task.id))
            .group_by(Task.status)
            .all()
        )

        priority_labels = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}
        priority_counts = dict(
            db.session.query(Task.priority, func.count(Task.id))
            .group_by(Task.priority)
            .all()
        )

        all_tasks = Task.query.all()
        overdue_list = [
            {
                'id': t.id,
                'title': t.title,
                'due_date': str(t.due_date),
                'days_overdue': (now - t.due_date).days,
            }
            for t in all_tasks if t.is_overdue()
        ]

        recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
        recent_done = Task.query.filter(
            Task.status == 'done',
            Task.updated_at >= seven_days_ago,
        ).count()

        user_task_stats = (
            db.session.query(
                Task.user_id,
                func.count(Task.id).label('total'),
                func.sum(case((Task.status == 'done', 1), else_=0)).label('done'),
            )
            .filter(Task.user_id.isnot(None))
            .group_by(Task.user_id)
            .all()
        )
        stat_by_uid = {row.user_id: row for row in user_task_stats}

        user_productivity = []
        for u in User.query.all():
            row = stat_by_uid.get(u.id)
            total = row.total if row else 0
            done = row.done if row else 0
            user_productivity.append({
                'user_id': u.id,
                'user_name': u.name,
                'total_tasks': total,
                'completed_tasks': done,
                'completion_rate': calculate_percentage(done, total),
            })

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': total_tasks,
                'total_users': total_users,
                'total_categories': total_categories,
            },
            'tasks_by_status': {
                'pending': status_counts.get('pending', 0),
                'in_progress': status_counts.get('in_progress', 0),
                'done': status_counts.get('done', 0),
                'cancelled': status_counts.get('cancelled', 0),
            },
            'tasks_by_priority': {
                label: priority_counts.get(num, 0)
                for num, label in priority_labels.items()
            },
            'overdue': {
                'count': len(overdue_list),
                'tasks': overdue_list,
            },
            'recent_activity': {
                'tasks_created_last_7_days': recent_tasks,
                'tasks_completed_last_7_days': recent_done,
            },
            'user_productivity': user_productivity,
        }

    @staticmethod
    def user_report(user_id):
        tasks = Task.query.filter_by(user_id=user_id).all()
        total = len(tasks)
        counts = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
        overdue = 0
        high_priority = 0

        for t in tasks:
            if t.status in counts:
                counts[t.status] += 1
            if t.priority <= 2:
                high_priority += 1
            if t.is_overdue():
                overdue += 1

        return {
            'statistics': {
                'total_tasks': total,
                'done': counts['done'],
                'pending': counts['pending'],
                'in_progress': counts['in_progress'],
                'cancelled': counts['cancelled'],
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': calculate_percentage(counts['done'], total),
            }
        }
