import time

############################################################################################################
# class timer
############################################################################################################

class timer:
  _my_logger = None
  def __init__(self, log_handle=None):
    self._start = time.time()
    self._my_logger = log_handle
    self._my_logger.info(f"Timer started at {self._start}")

  def start(self):
    self._start = time.time()
    self._my_logger.info(f"Timer started at {self._start}")
    return self._start

  def time_passed(self):
    self._stop = time.time()
    self._my_logger.info(f"Timer value = {self._stop - self._start}")
    return self._stop - self._start

