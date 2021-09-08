import heapq
import random
import time
from threading import Thread


class HeapExecutor(Thread):

    def run(self) -> None:
        global _last_tick
        global _tick_time
        global _pool0

        while True:

            now = time.time()

            while (now - _last_tick) + 0.0005 < _tick_time:

                if len(_pool0) > 0:
                    priority, func, arg = heapq.heappop(_pool0)
                    func(*arg)
                    now = time.time()
                    time.sleep(random.randint(1, 10) * 0.000001)
                else:
                    time.sleep(abs(_tick_time - (time.time() - _last_tick)))
                    break
            time.sleep(0)


_pool0 = []

_last_tick = time.time()
_tick_time = 1 / 60
_executor = HeapExecutor()
_executor.setDaemon(True)
_executor.start()


class _PriorityTuple(tuple):

    def __lt__(self, x) -> bool:
        return self[0] < x[0]

    def __le__(self, x) -> bool:
        return self[0] <= x[0]

    def __gt__(self, x) -> bool:
        return self[0] > x[0]

    def __ge__(self, x) -> bool:
        return self[0] >= x[0]


def tick(fps):
    global _last_tick
    global _tick_time
    global _executor
    _last_tick = time.time()
    _tick_time = 1 / fps

    if not _executor.is_alive():
        _executor = HeapExecutor()
        _executor.start()


def run_in_thread(func, args, priority: int = 0):
    heapq.heappush(_pool0, _PriorityTuple((priority, func, args)))
