class CustomFlag(object):
    """Class responsible of creating and handling a flag (set, clear, is_set)"""
    
    def __init__(self) -> None:
        super().__init__()
        self.reset()

    def set(self, val:bool=True):
        """Set the flag"""
        self._set_old()
        self.flag=val
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
    max_time:float=1.0
    time_stp:float=0.1
    cnt:int=0
    max_cnt:int

    def __init__(self, max_time:float=1.0, time_stp:float=0.1) -> None:
        super().__init__()
        self.set_max_time(max_time)
        self.set_time_stp(time_stp)
        self.reset()

    def increment(self)->bool:
        # print('cnt', self.cnt, self.max_cnt, self.step, self._is_done())
        if self._is_done():
            self.reset()
            return True
        else:
            self.cnt+=1
            return False
    
    def reset(self)->None:
        self.cnt=0

    def set_max_time(self, max_time:float=1.0)->None:
        self.max_time=max_time
        self.set_counter()  

    def set_time_stp(self, time_stp:float=0.1)->None:
        self.time_stp=time_stp  
        self.set_counter()  

    def _is_done(self)->bool:
        return self.max_cnt==self.cnt
    
    def is_rst(self)->bool:
        return bool(self.cnt)

    def set_counter(self):
        self.max_cnt= int(self.max_time/self.time_stp)
        