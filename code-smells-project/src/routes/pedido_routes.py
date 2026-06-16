from flask import Blueprint, request
from controllers.pedido_controller import PedidoController

pedido_bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")


@pedido_bp.route("", methods=["POST"])
def criar():
    return PedidoController.criar(request.get_json())


@pedido_bp.route("", methods=["GET"])
def listar_todos():
    return PedidoController.listar_todos()


@pedido_bp.route("/usuario/<int:usuario_id>", methods=["GET"])
def listar_por_usuario(usuario_id):
    return PedidoController.listar_por_usuario(usuario_id)


@pedido_bp.route("/<int:pedido_id>/status", methods=["PUT"])
def atualizar_status(pedido_id):
    return PedidoController.atualizar_status(pedido_id, request.get_json())
