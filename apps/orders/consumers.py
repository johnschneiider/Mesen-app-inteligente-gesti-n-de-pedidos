import json
from channels.generic.websocket import AsyncWebsocketConsumer


class OrderConsumer(AsyncWebsocketConsumer):
    """
    Canal WebSocket por negocio: business_<id>
    El dueño del negocio se conecta al abrir "Pedidos en vivo".
    Cuando llega un nuevo pedido o cambia de estado, se pushea al grupo.
    """

    async def connect(self):
        user = self.scope['user']
        if not user.is_authenticated or not user.is_business_owner:
            await self.close()
            return
        try:
            business = user.business
        except Exception:
            await self.close()
            return

        self.business_id = business.id
        self.group_name = f'business_{self.business_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # El cliente no envía mensajes en esta versión
        pass

    async def order_update(self, event):
        """Recibe evento del grupo y lo manda al WebSocket."""
        await self.send(text_data=json.dumps(event['payload']))
