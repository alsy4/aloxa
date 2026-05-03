import queue
import threading


class EventBroker:
    """In-process fan-out: publishers push events; each subscriber gets its own queue."""

    def __init__(self, max_queue: int = 50):
        self._subscribers: list[queue.Queue] = []
        self._lock = threading.Lock()
        self._max_queue = max_queue

    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=self._max_queue)
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def publish(self, event: dict) -> None:
        with self._lock:
            subs = list(self._subscribers)
        for q in subs:
            try:
                q.put_nowait(event)
            except queue.Full:
                # drop events for slow consumers rather than blocking the publisher
                pass
