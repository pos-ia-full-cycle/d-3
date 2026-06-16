"""Script para popular o banco com dados iniciais"""
from datetime import datetime, timedelta, timezone
from app import app
from src.database import db
from src.models.task import Task
from src.models.user import User
from src.models.category import Category


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def seed_data():
    with app.app_context():
        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        u1 = User(name='João Silva', email='joao@email.com', role='admin')
        u1.set_password('admin1234')

        u2 = User(name='Maria Santos', email='maria@email.com', role='user')
        u2.set_password('user1234')

        u3 = User(name='Pedro Oliveira', email='pedro@email.com', role='manager')
        u3.set_password('manager1234')

        db.session.add_all([u1, u2, u3])
        db.session.commit()

        c1 = Category(name='Backend', description='Tarefas de backend', color='#3498db')
        c2 = Category(name='Frontend', description='Tarefas de frontend', color='#2ecc71')
        c3 = Category(name='DevOps', description='Tarefas de infraestrutura', color='#e74c3c')
        c4 = Category(name='Bug', description='Correção de bugs', color='#e67e22')

        db.session.add_all([c1, c2, c3, c4])
        db.session.commit()

        now = _utcnow()
        tasks_data = [
            {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': 'pending', 'priority': 1, 'user': u1, 'category': c1, 'due_date': now - timedelta(days=3)},
            {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': 'in_progress', 'priority': 2, 'user': u2, 'category': c2, 'due_date': now + timedelta(days=5)},
            {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': 'done', 'priority': 2, 'user': u3, 'category': c3, 'tags': 'devops,ci,github'},
            {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': 'pending', 'priority': 1, 'user': u1, 'category': c4, 'due_date': now - timedelta(days=1)},
            {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': 'pending', 'priority': 3, 'user': u1, 'category': c1, 'due_date': now + timedelta(days=10)},
            {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': 'pending', 'priority': 2, 'user': u2, 'category': c1},
            {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': 'cancelled', 'priority': 4, 'user': u3, 'category': c1},
            {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': 'in_progress', 'priority': 3, 'user': u2, 'category': c1, 'tags': 'refactor,tech-debt'},
            {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': 'pending', 'priority': 4, 'user': u3, 'category': c3, 'due_date': now + timedelta(days=20)},
            {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': 'pending', 'priority': 3, 'user': u1, 'category': c1, 'tags': 'improvement,validation'},
        ]

        for td in tasks_data:
            t = Task(
                title=td['title'],
                description=td['description'],
                status=td['status'],
                priority=td['priority'],
                user_id=td['user'].id,
                category_id=td['category'].id,
                due_date=td.get('due_date'),
                tags=td.get('tags'),
            )
            db.session.add(t)

        db.session.commit()
        print("Seed concluído com sucesso!")
        print(f"  {User.query.count()} usuários")
        print(f"  {Category.query.count()} categorias")
        print(f"  {Task.query.count()} tasks")


if __name__ == '__main__':
    seed_data()
