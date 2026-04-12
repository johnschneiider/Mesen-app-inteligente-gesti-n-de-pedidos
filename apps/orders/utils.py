from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def notify_order_update(business_id: int, payload: dict):
    """Dispara un evento WebSocket al grupo del negocio."""
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        f'business_{business_id}',
        {'type': 'order_update', 'payload': payload},
    )
