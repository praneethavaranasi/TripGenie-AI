import asyncio
from typing import Dict, List


class EventManager:
    def __init__(self):
        self.clients: Dict[str, List[asyncio.Queue]] = {}

    async def subscribe(self, request_id: str):
        queue = asyncio.Queue()

        if request_id not in self.clients:
            self.clients[request_id] = []

        self.clients[request_id].append(queue)

        try:
            yield {"type": "ready"}

            while True:
                event = await queue.get()
                yield event

                if event.get("type") == "complete":
                    break

        finally:
            if request_id in self.clients:
                if queue in self.clients[request_id]:
                    self.clients[request_id].remove(queue)

                if not self.clients[request_id]:
                    del self.clients[request_id]

    async def publish(
        self,
        request_id: str,
        event: dict,
    ):
        queues = self.clients.get(request_id, [])

        for queue in queues:
            await queue.put(event)


event_manager = EventManager()
