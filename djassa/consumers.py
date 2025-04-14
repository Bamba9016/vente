import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({
            'message': 'Connexion établie avec WebSocket !'
        }))

    async def disconnect(self, close_code):
        print("WebSocket déconnecté")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        print("Message reçu :", message)

        await self.send(text_data=json.dumps({
            'message': message
        }))
