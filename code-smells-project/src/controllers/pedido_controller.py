import logging
from flask import jsonify
from database import commit_db
from models.usuario_model import UsuarioModel
from models.pedido_model import PedidoModel
from services.pedido_service import PedidoService
from services.notificacao_service import NotificacaoService

logger = logging.getLogger(__name__)

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


class PedidoController:
    @staticmethod
    def criar(dados):
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])
        if not usuario_id:
            return jsonify({"erro": "Usuario ID é obrigatório"}), 400
        if not itens:
            return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400
        if not UsuarioModel.find_by_id(usuario_id):
            return jsonify({"erro": "Usuário não encontrado"}), 404
        resultado = PedidoService.criar_pedido(usuario_id, itens)
        NotificacaoService.notificar_novo_pedido(resultado["pedido_id"], usuario_id)
        return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201

    @staticmethod
    def listar_todos():
        pedidos = PedidoModel.find_all()
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    @staticmethod
    def listar_por_usuario(usuario_id):
        pedidos = PedidoModel.find_by_usuario(usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    @staticmethod
    def atualizar_status(pedido_id, dados):
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        novo_status = dados.get("status", "")
        if novo_status not in STATUS_VALIDOS:
            return jsonify({"erro": "Status inválido"}), 400
        PedidoModel.update_status(pedido_id, novo_status)
        commit_db()
        NotificacaoService.notificar_status_pedido(pedido_id, novo_status)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
