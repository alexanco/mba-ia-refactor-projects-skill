def notificar_pedido_criado(pedido_id, usuario_id):
    """
    Notify the user that their order was received.
    TODO: Integrate with email provider (e.g. SendGrid), SMS (e.g. Twilio),
          and push notification service.
    """
    pass


def notificar_pedido_aprovado(pedido_id):
    """
    Notify fulfillment team that an order was approved and is ready to ship.
    TODO: Integrate with warehouse/fulfillment webhook.
    """
    pass


def notificar_pedido_cancelado(pedido_id):
    """
    Notify relevant parties of cancellation so stock can be restored if needed.
    TODO: Trigger stock reconciliation and customer refund flow.
    """
    pass
