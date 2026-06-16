from flask import Blueprint
from controllers.relatorio_controller import RelatorioController

relatorio_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")


@relatorio_bp.route("/vendas", methods=["GET"])
def vendas():
    return RelatorioController.vendas()
