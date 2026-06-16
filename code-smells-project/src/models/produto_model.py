from database import get_db

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]


def _row_to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


class ProdutoModel:
    @staticmethod
    def find_all():
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM produtos WHERE ativo = 1")
        return [_row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def find_by_id(produto_id):
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
        row = cursor.fetchone()
        return _row_to_dict(row) if row else None

    @staticmethod
    def search(termo="", categoria=None, preco_min=None, preco_max=None):
        query = "SELECT * FROM produtos WHERE ativo = 1"
        params = []
        if termo:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            params.extend([f"%{termo}%", f"%{termo}%"])
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        if preco_min is not None:
            query += " AND preco >= ?"
            params.append(preco_min)
        if preco_max is not None:
            query += " AND preco <= ?"
            params.append(preco_max)
        cursor = get_db().cursor()
        cursor.execute(query, params)
        return [_row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def create(nome, descricao, preco, estoque, categoria):
        cursor = get_db().cursor()
        cursor.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        return cursor.lastrowid

    @staticmethod
    def update(produto_id, nome, descricao, preco, estoque, categoria):
        cursor = get_db().cursor()
        cursor.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )

    @staticmethod
    def delete(produto_id):
        cursor = get_db().cursor()
        cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    @staticmethod
    def decrement_stock(produto_id, quantidade):
        cursor = get_db().cursor()
        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (quantidade, produto_id),
        )
