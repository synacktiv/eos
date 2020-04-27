"""
EOS Queue.

Simple wrapper on queue.Queue to provides additional features.
Queue.join() has a heartbeat mechanism to regularly output its status.
Queue.clear() clears the queue.
"""

from queue import Queue as _Queue

from eos.core import Base


class Queue(_Queue, Base):
    """
    EOS Queue.

    Override the join() method to add heartbeats.
    The queue then output its status with a regular heartbeat.
    Provides a clear() method to clear the enqueued tasks.
    """

    def join(self, heartbeat=30):
        """
        Wrapper on Queue.join().

        Output the current status with a regular heartbeat.
        Simply override the default behavior by adding a timeout parameter.

        :param heartbeat: interval in seconds
        """

        with self.all_tasks_done:
            while self.unfinished_tasks:
                got_it = self.all_tasks_done.wait(timeout=heartbeat)
                if not got_it:
                    self.log.info('Queue: %d left', self.unfinished_tasks)

    def clear(self):
        """Clear the queue."""
        self.queue.clear()
