import logging

logger = logging.getLogger(__name__)


class NotificacaoService:
    @staticmethod
    def notificar_novo_pedido(pedido_id, usuario_id):
        logger.info(f"[EMAIL] Pedido {pedido_id} criado para usuário {usuario_id}")
        logger.info("[SMS] Seu pedido foi recebido!")
        logger.info("[PUSH] Novo pedido recebido pelo sistema")

    @staticmethod
    def notificar_status_pedido(pedido_id, novo_status):
        if novo_status == "aprovado":
            logger.info(f"[NOTIFICAÇÃO] Pedido {pedido_id} aprovado. Preparar envio.")
        elif novo_status == "cancelado":
            logger.info(f"[NOTIFICAÇÃO] Pedido {pedido_id} cancelado. Devolver estoque.")
