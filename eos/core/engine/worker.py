"""
HTTP Workers module.

Workers register to a queue from where they receive HTTP request to issue.
They process them using the requests package and responses are added
to a global results list passed on initialization.
"""

from threading import Thread, Event

from requests import Session

from eos.core import Base


class Worker(Thread, Base):
    """
    EOS Worker.

    Worker dedicated to issuing requests and saving responses.
    """

    def __init__(self, queue, results, *args, session=None, **kwargs):
        """
        Initialization.

        :param queue: queue to get the URLs from
        :param results: list holding the results
        :param session: requests session
        """

        super().__init__(*args, **kwargs)

        self.queue = queue
        self.results = results
        self.session = session or Session()
        self.shutdown = Event()

    def run(self):
        """
        Running loop.

        Get requests from the queue and process them.
        Mark the task as done.
        The loop ends when None is fetched from the queue.
        """

        while not self.shutdown.is_set():
            request = self.queue.get()
            if request is None:
                break
            try:
                self.process(request)
            except Exception as error:
                self.log.exception('%s', error)
            self.queue.task_done()

    def process(self, request):
        """
        Process the request.

        Prepare and issue the request.
        Response is logged and attached to the request.
        The original request is finally added to the results.

        :param request: the unprepared request to process
        """

        response = self.session.send(request.prepare())
        response.request = request
        self.log.debug('[%d] %s', response.status_code, response.url)
        self.results.append(response)

    def join(self, *args, **kwargs):
        """Set the sentinel and join."""
        self.shutdown.set()
        super().join(*args, **kwargs)
