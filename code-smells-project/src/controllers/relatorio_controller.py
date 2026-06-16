from flask import jsonify
from services.relatorio_service import RelatorioService


class RelatorioController:
    @staticmethod
    def vendas():
        relatorio = RelatorioService.relatorio_vendas()
        return jsonify({"dados": relatorio, "sucesso": True}), 200
