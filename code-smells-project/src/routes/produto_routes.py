from flask import Blueprint, request
from controllers.produto_controller import ProdutoController

produto_bp = Blueprint("produtos", __name__, url_prefix="/produtos")


@produto_bp.route("", methods=["GET"])
def listar():
    return ProdutoController.listar()


@produto_bp.route("/busca", methods=["GET"])
def buscar_por_filtros():
    return ProdutoController.buscar_por_filtros(
        request.args.get("q", ""),
        request.args.get("categoria"),
        request.args.get("preco_min"),
        request.args.get("preco_max"),
    )


@produto_bp.route("/<int:produto_id>", methods=["GET"])
def buscar(produto_id):
    return ProdutoController.buscar(produto_id)


@produto_bp.route("", methods=["POST"])
def criar():
    return ProdutoController.criar(request.get_json())


@produto_bp.route("/<int:produto_id>", methods=["PUT"])
def atualizar(produto_id):
    return ProdutoController.atualizar(produto_id, request.get_json())


@produto_bp.route("/<int:produto_id>", methods=["DELETE"])
def deletar(produto_id):
    return ProdutoController.deletar(produto_id)
