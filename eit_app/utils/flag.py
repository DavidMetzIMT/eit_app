class Flag(object):
    """Class responsible of creating and handling a flag (set, clear, is_set)"""
    flag:bool=False
    def set(self):
        """Set the flag"""
        self.flag=True
    def clear(self):
        """clear the flag"""
        self.flag=False
    def is_set(self):
        """Return value of the flag"""
        return self.flag