from src.models.database import get_db


def criar_pedido(usuario_id, itens):
    db = get_db()
    cursor = db.cursor()

    total = 0
    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (item["produto_id"],))
        produto = cursor.fetchone()
        if produto is None:
            return {"erro": f"Produto {item['produto_id']} não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": f"Estoque insuficiente para {produto['nome']}"}
        total += produto["preco"] * item["quantidade"]

    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total)
    )
    pedido_id = cursor.lastrowid

    for item in itens:
        cursor.execute("SELECT preco FROM produtos WHERE id = ?", (item["produto_id"],))
        produto = cursor.fetchone()
        cursor.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            (pedido_id, item["produto_id"], item["quantidade"], produto["preco"])
        )
        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], item["produto_id"])
        )

    db.commit()
    return {"pedido_id": pedido_id, "total": total}


def get_pedidos_usuario(usuario_id):
    return _get_pedidos_com_itens("WHERE p.usuario_id = ?", (usuario_id,))


def get_todos_pedidos():
    return _get_pedidos_com_itens("", ())


def atualizar_status_pedido(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?",
        (novo_status, pedido_id)
    )
    db.commit()
    return True


def relatorio_vendas():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM pedidos")
    row = cursor.fetchone()
    total_pedidos = row[0]
    faturamento = row[1]

    cursor.execute("SELECT status, COUNT(*) FROM pedidos GROUP BY status")
    status_counts = {r[0]: r[1] for r in cursor.fetchall()}

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "pedidos_pendentes": status_counts.get("pendente", 0),
        "pedidos_aprovados": status_counts.get("aprovado", 0),
        "pedidos_cancelados": status_counts.get("cancelado", 0),
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }


def _get_pedidos_com_itens(where_clause, params):
    """Fetch orders with all items using a single JOIN query (eliminates N+1)."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"""
        SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
               ip.produto_id, ip.quantidade, ip.preco_unitario, pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = ip.produto_id
        {where_clause}
        ORDER BY p.id
    """, params)

    rows = cursor.fetchall()
    pedidos = {}
    for row in rows:
        pid = row["id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": pid,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": []
            }
        if row["produto_id"] is not None:
            pedidos[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"]
            })
    return list(pedidos.values())
