from flask import Blueprint, request
from controllers.usuario_controller import UsuarioController

usuario_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@usuario_bp.route("", methods=["GET"])
def listar():
    return UsuarioController.listar()


@usuario_bp.route("/<int:usuario_id>", methods=["GET"])
def buscar(usuario_id):
    return UsuarioController.buscar(usuario_id)


@usuario_bp.route("", methods=["POST"])
def criar():
    return UsuarioController.criar(request.get_json())
