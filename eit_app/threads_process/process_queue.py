import multiprocessing
from multiprocessing.queues import Queue


class NewQueue(Queue):
    def __init__(self,*args,**kwargs):
        ctx = multiprocessing.get_context()
        super().__init__(*args,**kwargs, ctx=ctx)
    
    def to_list(self):
        """
        Returns a copy of all items in the queue without removing them.
        """
        return list(self._buffer)
