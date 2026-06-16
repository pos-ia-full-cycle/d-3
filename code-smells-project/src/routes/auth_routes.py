from flask import Blueprint, request
from controllers.usuario_controller import UsuarioController

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    return UsuarioController.login(request.get_json())
