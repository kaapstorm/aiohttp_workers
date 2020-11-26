aiohttp workers
===============

An example of using asyncio within multiple processes to fetch URLs.

Spawns a process worker for each CPU core. Each process worker runs
a number of async workers, set in `workers.TASKS_PER_PROCESS`.

All URLs are dumped into a master queue. URLs are then taken roughly
evenly by each process worker into its own async queue for its async
workers.

Room for improvement: For an indefinite number of items, this example
would need to use better queue management.


Install
-------

    $ python3 -v venv venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt


Run
---

    $ python3 workers.py
