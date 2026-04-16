from flask import request, jsonify
from src.models import pedido_model
from src.services import notification_service
from src.services.relatorio_service import gerar_relatorio_vendas

STATUSES_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


def criar_pedido():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return jsonify({"erro": "Usuario ID é obrigatório"}), 400
    if not itens:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

    resultado = pedido_model.criar_pedido(usuario_id, itens)
    if "erro" in resultado:
        return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

    notification_service.notificar_pedido_criado(resultado["pedido_id"], usuario_id)

    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar_pedidos_usuario(usuario_id):
    pedidos = pedido_model.get_pedidos_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos_pedidos():
    pedidos = pedido_model.get_todos_pedidos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    novo_status = dados.get("status", "")
    if novo_status not in STATUSES_VALIDOS:
        return jsonify({"erro": "Status inválido"}), 400

    pedido_model.atualizar_status_pedido(pedido_id, novo_status)

    if novo_status == "aprovado":
        notification_service.notificar_pedido_aprovado(pedido_id)
    elif novo_status == "cancelado":
        notification_service.notificar_pedido_cancelado(pedido_id)

    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


def relatorio_vendas():
    relatorio = gerar_relatorio_vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200
