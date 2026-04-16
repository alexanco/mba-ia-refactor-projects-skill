from flask import Blueprint, jsonify, request
from src.config.settings import Config

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/reset-db', methods=['POST'])
def reset_database():
    """
    WARNING: Destructive endpoint — deletes all data.
    Restricted to DEBUG mode only. Remove before production deployment.
    """
    if not Config.DEBUG:
        return jsonify({"erro": "Endpoint não disponível em produção"}), 403

    from src.models.database import get_db
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
    db.commit()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


@admin_bp.route('/admin/query', methods=['POST'])
def executar_query():
    """
    WARNING: Arbitrary SQL execution endpoint.
    Restricted to DEBUG mode only. Remove before production deployment.
    """
    if not Config.DEBUG:
        return jsonify({"erro": "Endpoint não disponível em produção"}), 403

    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    query = dados.get("sql", "")
    if not query:
        return jsonify({"erro": "Query não informada"}), 400

    from src.models.database import get_db
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(query)
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            return jsonify({"dados": result, "sucesso": True}), 200
        else:
            db.commit()
            return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
