import time
import logging
import serial

############################################################################################################
# class bg95_serial
############################################################################################################

class bg95_serial:
  _port = None
  _baudrate = None
  _ser = None
  _connected = False
  _my_logger = None
  _default_timeout = 0

  def __init__(self, log_handle=None, port='COM11', baudrate=115200, default_timeout = 1):
    self._my_logger = log_handle
    self._port = port
    self._baudrate = baudrate
    self._default_timeout = 0
    pass

  def open_usb(self):
    try:
      self._ser = serial.Serial(port=self._port, baudrate=self._baudrate, timeout=self._default_timeout)
    except Exception as e:
      self._my_logger.error(f"Error: {e}")
      return False

    if self._ser.is_open:
      self._my_logger.debug(f"Serial port {self._port} is open.")
      self._my_logger.debug(self._ser.name)
      self._connected = True
      return True
    else:
      self._my_logger.error(f"Failed to open serial port {self._port}.")
      return False

  def close_usb(self):
    # Close the serial port
    self._ser.close()
    self._connected = False
    self._my_logger.debug(f"Serial port {self._port} is closed.")

  def _write_line(self, command):
    if self._connected:
        try:
            # Write data to the serial port
            self._ser.write(command.encode('utf-8') + b'\r')
            return True 
        except Exception as e:
            self._my_logger.error(f"Error: {e}")
            return False
    else:
      self._my_logger.error(f"Serial port {self._port} is closed.")
      return False

  def _read_line(self, timeout=_default_timeout):
    if self._connected:
        try:
          self._ser.timeout = timeout
          # _read data from the serial port
          response = self._ser.readline().decode().strip()
          # self._my_logger.debug(f"Received: {response}")
          return True, response
        except Exception as e:
            self._my_logger.error(f"Error: {e}")
            return False, None
    else:
      self._my_logger.error(f"Serial port {self._port} is closed.")
      return False, None
