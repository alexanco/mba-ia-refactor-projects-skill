from flask import Blueprint
from src.controllers import pedido_controller

pedido_bp = Blueprint('pedidos', __name__)


@pedido_bp.route('/pedidos', methods=['POST'])
def criar():
    return pedido_controller.criar_pedido()


@pedido_bp.route('/pedidos', methods=['GET'])
def listar_todos():
    return pedido_controller.listar_todos_pedidos()


@pedido_bp.route('/pedidos/usuario/<int:usuario_id>', methods=['GET'])
def listar_usuario(usuario_id):
    return pedido_controller.listar_pedidos_usuario(usuario_id)


@pedido_bp.route('/pedidos/<int:pedido_id>/status', methods=['PUT'])
def atualizar_status(pedido_id):
    return pedido_controller.atualizar_status_pedido(pedido_id)


@pedido_bp.route('/relatorios/vendas', methods=['GET'])
def relatorio():
    return pedido_controller.relatorio_vendas()
