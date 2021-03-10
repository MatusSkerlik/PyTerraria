import asyncio
import heapq
import time
from asyncio import CancelledError
from functools import partial

import pygame

fps = 70
_loop = asyncio.get_event_loop()
_pool0 = []

_last_tick = time.time()
_tick_time = 1 / fps
_clock = pygame.time.Clock()


class _PriorityTuple(tuple):

    def __lt__(self, x) -> bool:
        return self[0] < x[0]

    def __le__(self, x) -> bool:
        return self[0] <= x[0]

    def __gt__(self, x) -> bool:
        return self[0] > x[0]

    def __ge__(self, x) -> bool:
        return self[0] >= x[0]


def run_coroutine(coroutine, on_success, on_error, priority: int = 0):
    heapq.heappush(_pool0, _PriorityTuple((priority, coroutine, on_success, on_error)))


def _handle_callbacks(on_success, on_error, future):
    try:
        result = future.result()
        if on_success:
            on_success(result)
    except CancelledError as e:
        if on_error:
            on_error(e)


async def _consume_coroutines():
    """ Consumes coroutines in pool if there is time left """

    global _last_tick
    now = time.time()
    while (now - _last_tick) + 0.001 < _tick_time:
        try:
            priority, coroutine, on_success, on_error = heapq.heappop(_pool0)
            task = _loop.create_task(coroutine)
            task.add_done_callback(partial(_handle_callbacks, on_success, on_error))

            try:
                time_left = float(_tick_time - (now - _last_tick))
                await asyncio.wait_for(task, time_left)  # TODO not working
            except TimeoutError as e:
                on_error(e)

            now = time.time()
        except IndexError:
            break


async def tick():
    """ Tick in separated thread for awaited coroutines in pool to be processed """

    global _last_tick
    now = time.time()
    passed = now - _last_tick

    if passed < _tick_time:  # time for background execution left, execute background tasks
        _loop.create_task(_consume_coroutines())
        await _loop.run_in_executor(None, _clock.tick, fps)
        _last_tick = time.time()
        return _clock.get_time() / 1000
    else:  # main loop execution time exhausted, return dt immediately
        _clock.tick(fps)
        _last_tick = time.time()
        return _clock.get_time() / 1000


def run_async(coroutine):
    """ Main entry for async application  """
    global _loop
    _loop = asyncio.get_event_loop()
    _loop.run_until_complete(coroutine)
    _loop.close()
