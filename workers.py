import asyncio
import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from math import ceil
from queue import Empty

import aiohttp

NUM_PROCESSES = multiprocessing.cpu_count()
TASKS_PER_PROCESS = 16
NUM_ITEMS = 1023


def get_all_items():
    """
    Generates the URLs to be fetched.
    """
    for _ in range(NUM_ITEMS):
        yield 'http://localhost:10080/get'


def run_process_workers():
    manager = multiprocessing.Manager()
    master_queue = manager.Queue()
    for url in get_all_items():
        master_queue.put_nowait(url)

    with ProcessPoolExecutor(max_workers=NUM_PROCESSES) as executor:
        futures = {executor.submit(process_worker, n, master_queue)
                   for n in range(NUM_PROCESSES)}
        for future in as_completed(futures):
            print(future.result())


def process_worker(number: int, master_queue) -> str:
    name = f'process_worker_{number}'
    future = run_async_workers(master_queue)
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(future)
    return f'{name}: {result}'


async def run_async_workers(master_queue) -> str:
    queue = populate_queue_from_master_queue(master_queue)
    tasks = [asyncio.create_task(async_worker(queue))
             for _ in range(TASKS_PER_PROCESS)]

    started_at = time.monotonic()
    await queue.join()
    duration = time.monotonic() - started_at

    for task in tasks:
        task.cancel()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return f'{sum(results)} urls in {duration:.2f}s'


async def async_worker(queue) -> int:
    count = 0
    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            while True:
                url = await queue.get()
                async with session.get(url) as response:
                    ok = 200 <= response.status < 300
                    #json = await response.json()
                    #ok = bool(json)
                queue.task_done()
                # print('.' if ok else 'x', end='')
                count += 1
        finally:
            # Returns count instead of asyncio.CancelledError when the
            # task is cancelled
            return count


def populate_queue_from_master_queue(master_queue) -> asyncio.Queue:
    queue = asyncio.Queue()
    num_items = ceil(NUM_ITEMS / NUM_PROCESSES)
    for _ in range(num_items):
        try:
            url = master_queue.get_nowait()
        except Empty:
            break
        else:
            queue.put_nowait(url)
    return queue


if __name__ == '__main__':
    run_process_workers()
