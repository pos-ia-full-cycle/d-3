from flask import Blueprint
from src.controllers.task_controller import TaskController

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return TaskController.get_all()


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    return TaskController.search()


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return TaskController.stats()


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    return TaskController.get_one(task_id)


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    return TaskController.create()


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    return TaskController.update(task_id)


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    return TaskController.delete(task_id)
