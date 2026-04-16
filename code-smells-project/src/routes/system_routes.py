from flask import Blueprint
from src.controllers.system_controller import health_check

system_bp = Blueprint('system', __name__)


@system_bp.route('/health', methods=['GET'])
def health():
    return health_check()
