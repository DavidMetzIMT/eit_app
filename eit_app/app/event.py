

class CustomEvents:
    
    def __init__(self) -> None:
        self.subscribers = {}

    def subscribe(self, event_type: str, fn):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(fn)

    def post(self,event_type: str, *args):
        if event_type not in self.subscribers:
            return
        for fn in self.subscribers[event_type]:
            fn(*args)