from models.pedido_model import PedidoModel

DISCOUNT_TIERS = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]


class RelatorioService:
    @staticmethod
    def relatorio_vendas():
        stats = PedidoModel.get_raw_stats()
        faturamento = stats["faturamento"]
        total_pedidos = stats["total_pedidos"]

        desconto = next(
            (faturamento * rate for threshold, rate in DISCOUNT_TIERS if faturamento > threshold),
            0.0,
        )

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": stats["pendentes"],
            "pedidos_aprovados": stats["aprovados"],
            "pedidos_cancelados": stats["cancelados"],
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }
