from database import get_db

_PEDIDOS_JOIN_SQL = """
    SELECT p.id as pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
           ip.produto_id, ip.quantidade, ip.preco_unitario,
           pr.nome as produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = ip.produto_id
"""


def _build_pedidos_from_rows(rows):
    pedidos = {}
    for row in rows:
        pid = row["pedido_id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": pid,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
        if row["produto_id"] is not None:
            pedidos[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


class PedidoModel:
    @staticmethod
    def find_all():
        cursor = get_db().cursor()
        cursor.execute(_PEDIDOS_JOIN_SQL + " ORDER BY p.id")
        return _build_pedidos_from_rows(cursor.fetchall())

    @staticmethod
    def find_by_usuario(usuario_id):
        cursor = get_db().cursor()
        cursor.execute(
            _PEDIDOS_JOIN_SQL + " WHERE p.usuario_id = ? ORDER BY p.id",
            (usuario_id,),
        )
        return _build_pedidos_from_rows(cursor.fetchall())

    @staticmethod
    def create(usuario_id, total):
        cursor = get_db().cursor()
        cursor.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        return cursor.lastrowid

    @staticmethod
    def add_item(pedido_id, produto_id, quantidade, preco_unitario):
        cursor = get_db().cursor()
        cursor.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            (pedido_id, produto_id, quantidade, preco_unitario),
        )

    @staticmethod
    def update_status(pedido_id, novo_status):
        cursor = get_db().cursor()
        cursor.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?",
            (novo_status, pedido_id),
        )

    @staticmethod
    def get_raw_stats():
        cursor = get_db().cursor()
        cursor.execute("SELECT COUNT(*) as total, COALESCE(SUM(total), 0) as faturamento FROM pedidos")
        row = cursor.fetchone()
        total_pedidos = row["total"]
        faturamento = row["faturamento"]

        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
        pendentes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
        aprovados = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
        cancelados = cursor.fetchone()[0]

        return {
            "total_pedidos": total_pedidos,
            "faturamento": faturamento,
            "pendentes": pendentes,
            "aprovados": aprovados,
            "cancelados": cancelados,
        }
