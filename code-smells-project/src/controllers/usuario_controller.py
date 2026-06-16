import re
import logging
from flask import jsonify
from database import commit_db
from models.usuario_model import UsuarioModel

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UsuarioController:
    @staticmethod
    def listar():
        usuarios = UsuarioModel.find_all()
        return jsonify({"dados": usuarios, "sucesso": True}), 200

    @staticmethod
    def buscar(usuario_id):
        usuario = UsuarioModel.find_by_id(usuario_id)
        if not usuario:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        return jsonify({"dados": usuario, "sucesso": True}), 200

    @staticmethod
    def criar(dados):
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not nome or not email or not senha:
            return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400
        if not _EMAIL_RE.match(email):
            return jsonify({"erro": "Formato de email inválido"}), 400
        usuario_id = UsuarioModel.create(nome, email, senha)
        commit_db()
        logger.info(f"Usuário criado: {email}")
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    @staticmethod
    def login(dados):
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not email or not senha:
            return jsonify({"erro": "Email e senha são obrigatórios"}), 400
        usuario = UsuarioModel.find_by_email(email)
        if not usuario or not UsuarioModel.verify_password(senha, usuario["senha"]):
            logger.warning(f"Login falhou: {email}")
            return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
        logger.info(f"Login bem-sucedido: {email}")
        usuario_publico = {k: v for k, v in usuario.items() if k != "senha"}
        return jsonify({"dados": usuario_publico, "sucesso": True, "mensagem": "Login OK"}), 200
