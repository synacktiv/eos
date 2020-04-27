"""
EOS Engine package.
"""

from requests import Session

from eos.core import Base
from eos.core.engine.queue import Queue
from eos.core.engine.worker import Worker


class Engine(Base):
    """
    EOS engine.

    Instantiate workers and manage them.
    """

    def __init__(self, size, queue=None, session=None):
        """
        Initialization.

        :param size: number of workers
        :param queue: queue where workers will fetch tasks
        :param session: requests session
        """

        self.queue = queue or Queue()
        self.session = session or Session()
        self.size = size
        self.results = []
        self.workers = [Worker(self.queue, results=self.results, session=self.session) for _ in range(self.size)]

    def start(self):
        """Start workers."""
        self.log.debug('Starting engine (%d workers)', self.size)
        for worker in self.workers:
            worker.start()

    def stop(self):
        """Stop workers."""
        self.log.debug('Shutting engine down')
        self.queue.clear()
        for worker in self.workers:
            self.queue.put(None)
        for worker in self.workers:
            worker.join()

    def join(self):
        """Wait for the queue."""
        self.queue.join()

    def clear(self):
        """Clear queue and results."""
        self.queue.clear()
        self.results.clear()
