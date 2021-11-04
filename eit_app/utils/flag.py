class CustomFlag(object):
    """Class responsible of creating and handling a flag (set, clear, is_set)"""
    
    def __init__(self) -> None:
        super().__init__()
        self.reset()

    def set(self):
        """Set the flag"""
        self._set_old()
        self.flag=True
    def set_edge_up(self):
        """Set the flag"""
        self._set_old(False)
        self.flag=True
    def clear(self):
        """clear the flag"""
        self._set_old()
        self.flag=False
    def is_set(self):
        """Return value of the flag"""
        return self.flag
    def has_changed(self):
        return self.flag!=self.flag_old
    def is_raising_edge(self):
        return self.has_changed() and self.is_set()
    def reset(self):
        self.flag_old:bool=False
        self.flag:bool=False

    def ack_change(self):
        self._set_old()
    def _set_old(self, val:bool=None):
        self.flag_old=bool(self.flag) if not val else val



class CustomTimer(object):

    def __init__(self) -> None:
        super().__init__()
        self.max_cnt:float=0.0
        self.cnt:float=0.0
        self.step:float=1.0

    def increment(self)->bool:
        if self._is_done():
            self.cnt=self.step
            return 1
        else:
            self.cnt+=self.step
            return 0
    
    def reset(self):
        self.cnt=0.0
    
    def set_max_cnt(self, max_cnt):
        self.max_cnt=max_cnt
    def set_step(self, step):
        self.step=step    

    def _is_done(self)->bool:
        return self.max_cnt==self.cnt
