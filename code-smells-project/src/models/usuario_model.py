from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash


def _row_to_dict(row, include_senha=False):
    data = {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }
    if include_senha:
        data["senha"] = row["senha"]
    return data


class UsuarioModel:
    @staticmethod
    def find_all():
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM usuarios")
        return [_row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def find_by_id(usuario_id):
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
        row = cursor.fetchone()
        return _row_to_dict(row) if row else None

    @staticmethod
    def find_by_email(email):
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        row = cursor.fetchone()
        return _row_to_dict(row, include_senha=True) if row else None

    @staticmethod
    def create(nome, email, senha, tipo="cliente"):
        cursor = get_db().cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha, method="pbkdf2:sha256"), tipo),
        )
        return cursor.lastrowid

    @staticmethod
    def verify_password(senha_plain, senha_hash):
        return check_password_hash(senha_hash, senha_plain)
