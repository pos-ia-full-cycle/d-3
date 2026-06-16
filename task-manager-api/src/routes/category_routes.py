from flask import Blueprint
from src.controllers.category_controller import CategoryController

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    return CategoryController.get_all()


@category_bp.route('/categories', methods=['POST'])
def create_category():
    return CategoryController.create()


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    return CategoryController.update(cat_id)


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    return CategoryController.delete(cat_id)
