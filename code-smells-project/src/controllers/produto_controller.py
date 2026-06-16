import logging
from flask import jsonify
from database import commit_db
from models.produto_model import ProdutoModel, CATEGORIAS_VALIDAS

logger = logging.getLogger(__name__)


def _validate_produto_payload(dados):
    if not dados:
        raise ValueError("Dados inválidos")
    if "nome" not in dados:
        raise ValueError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValueError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValueError("Estoque é obrigatório")
    if dados["preco"] < 0:
        raise ValueError("Preço não pode ser negativo")
    if dados["estoque"] < 0:
        raise ValueError("Estoque não pode ser negativo")
    if len(dados["nome"]) < 2:
        raise ValueError("Nome muito curto")
    if len(dados["nome"]) > 200:
        raise ValueError("Nome muito longo")
    categoria = dados.get("categoria", "geral")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValueError(f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}")


class ProdutoController:
    @staticmethod
    def listar():
        produtos = ProdutoModel.find_all()
        logger.info(f"Listando {len(produtos)} produtos")
        return jsonify({"dados": produtos, "sucesso": True}), 200

    @staticmethod
    def buscar(produto_id):
        produto = ProdutoModel.find_by_id(produto_id)
        if not produto:
            return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
        return jsonify({"dados": produto, "sucesso": True}), 200

    @staticmethod
    def buscar_por_filtros(termo, categoria, preco_min, preco_max):
        if preco_min is not None:
            preco_min = float(preco_min)
        if preco_max is not None:
            preco_max = float(preco_max)
        resultados = ProdutoModel.search(termo, categoria, preco_min, preco_max)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    @staticmethod
    def criar(dados):
        _validate_produto_payload(dados)
        produto_id = ProdutoModel.create(
            dados["nome"],
            dados.get("descricao", ""),
            dados["preco"],
            dados["estoque"],
            dados.get("categoria", "geral"),
        )
        commit_db()
        logger.info(f"Produto criado com ID: {produto_id}")
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    @staticmethod
    def atualizar(produto_id, dados):
        produto = ProdutoModel.find_by_id(produto_id)
        if not produto:
            return jsonify({"erro": "Produto não encontrado"}), 404
        _validate_produto_payload(dados)
        ProdutoModel.update(
            produto_id,
            dados["nome"],
            dados.get("descricao", ""),
            dados["preco"],
            dados["estoque"],
            dados.get("categoria", "geral"),
        )
        commit_db()
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    @staticmethod
    def deletar(produto_id):
        produto = ProdutoModel.find_by_id(produto_id)
        if not produto:
            return jsonify({"erro": "Produto não encontrado"}), 404
        ProdutoModel.delete(produto_id)
        commit_db()
        logger.info(f"Produto {produto_id} deletado")
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
