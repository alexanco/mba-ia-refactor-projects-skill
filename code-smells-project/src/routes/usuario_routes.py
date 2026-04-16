from flask import Blueprint
from src.controllers import usuario_controller

usuario_bp = Blueprint('usuarios', __name__)


@usuario_bp.route('/usuarios', methods=['GET'])
def listar():
    return usuario_controller.listar_usuarios()


@usuario_bp.route('/usuarios/<int:id>', methods=['GET'])
def buscar(id):
    return usuario_controller.buscar_usuario(id)


@usuario_bp.route('/usuarios', methods=['POST'])
def criar():
    return usuario_controller.criar_usuario()


@usuario_bp.route('/login', methods=['POST'])
def login():
    return usuario_controller.login()
