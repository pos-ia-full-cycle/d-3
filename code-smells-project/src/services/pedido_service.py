import logging
from database import get_db
from models.produto_model import ProdutoModel
from models.pedido_model import PedidoModel

logger = logging.getLogger(__name__)


class PedidoService:
    @staticmethod
    def criar_pedido(usuario_id, itens):
        db = get_db()
        try:
            produtos_cache = {}
            for item in itens:
                produto = ProdutoModel.find_by_id(item["produto_id"])
                if produto is None:
                    raise ValueError(f"Produto {item['produto_id']} não encontrado")
                if produto["estoque"] < item["quantidade"]:
                    raise ValueError(f"Estoque insuficiente para {produto['nome']}")
                produtos_cache[item["produto_id"]] = produto

            total = sum(
                produtos_cache[item["produto_id"]]["preco"] * item["quantidade"]
                for item in itens
            )

            pedido_id = PedidoModel.create(usuario_id, total)
            for item in itens:
                produto = produtos_cache[item["produto_id"]]
                PedidoModel.add_item(pedido_id, item["produto_id"], item["quantidade"], produto["preco"])
                ProdutoModel.decrement_stock(item["produto_id"], item["quantidade"])

            db.commit()
            logger.info(f"Pedido {pedido_id} criado para usuário {usuario_id}, total={total}")
            return {"pedido_id": pedido_id, "total": total}
        except Exception:
            db.rollback()
            raise
