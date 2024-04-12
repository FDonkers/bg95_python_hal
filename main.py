import time
import serial
import logging
# https://realpython.com/python-logging/ 
logging.basicConfig(format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S', level=logging.DEBUG)

DEFAULT_TIMEOUT = 1

class Bg95_serial:
  _port = 'COM7'
  _baudrate = 115200
  _ser = None
  _connected = False

  def __init__(self):
    pass

  def connect(self):
    try:
      self._ser = serial.Serial(port=self._port, baudrate=self._baudrate, timeout=DEFAULT_TIMEOUT)
    except Exception as e:
      logging.error(f"Error: {e}")
      return False

    if self._ser.is_open:
      logging.debug(f"Serial port {self._port} is open.")
      logging.debug(self._ser.name)
      self._connected = True
      return True
    else:
      logging.error(f"Failed to open serial port {self._port}.")
      return False

  def close(self):
    # Close the serial port
    self._ser.close()
    self._connected = False
    logging.debug(f"Serial port {self._port} is closed.")

  def _write_line(self, command, timeout=DEFAULT_TIMEOUT):
    if self._connected:
        try:
            # Write data to the serial port
            self._ser.write(command.encode('utf-8') + b'\r')
            return True 
        except Exception as e:
            logging.error(f"Error: {e}")
            return False
    else:
      logging.error(f"Serial port {self._port} is closed.")
      return False

  def _read_line(self, timeout=DEFAULT_TIMEOUT):
    # logging.debug(f"timeout = {timeout}")
    if self._connected:
        try:
          self._ser.timeout = timeout
          # _read data from the serial port
          response = self._ser.readline().decode().strip()
          # logging.debug(f"Received: {response}")
          return True, response
        except Exception as e:
            logging.error(f"Error: {e}")
            return False, None
    else:
      logging.error(f"Serial port {self._port} is closed.")
      return False, None


class Bg95_cmd (Bg95_serial):
  _RESPONSE_OK = "OK"
  _RESPONSE_NOK = "ERROR"

  def __init__(self):
    pass

  def _read_echo(self, timeout=DEFAULT_TIMEOUT):
    # ToDo: check echo response
    return self._read_line(timeout)

  def _read_reponse(self, timeout=DEFAULT_TIMEOUT):
    return self._read_line()

  def _read_ok(self, timeout=DEFAULT_TIMEOUT):
    status, response = self._read_line(timeout)
    if status:
      return response == self._RESPONSE_OK
    else:
      return False

  def _send_atcmd(self, cmd="", timeout=DEFAULT_TIMEOUT):
    logging.debug(f"sending {cmd}")
    if not self._write_line(cmd):
      logging.error(f"not able to send {cmd}")
      return False, None

    if not self._read_echo(timeout):
      logging.error(f"did not receive echo for {cmd}")
      return False, None

    # collect response
    response = ""
    line = ""
    while line not in [self._RESPONSE_OK, self._RESPONSE_NOK]:
      status, line = self._read_reponse(timeout)
      if status:
        response += '< ' + line + "\n"
      else:
        logging.error(f"incomplete response for {cmd}")
        return False, None

    if line != self._RESPONSE_OK:
      logging.error(f"did not receive 'OK' for {cmd}")
      return False, None
    return True, response

  def _wait_for_urc(self, urc="", timeout=DEFAULT_TIMEOUT):
    while True:
      status, line = self._read_reponse(timeout)
      logging.debug(line)
      if status:
        if line == urc:
          return True
      else:
        logging.error(f"incomplete response for {urc}")
        return False

  def at(self):
    cmd = "AT"
    status, response = self._send_atcmd(cmd, 0)
    return status, response

  def ati(self):
    cmd = "ATI"
    status, response = self._send_atcmd(cmd, 4)
    return status, response

  def at_gsn(self):
    cmd = "AT+GSN"
    status, response = self._send_atcmd(cmd, 2)
    return status, response

  def at_v(self):
    cmd = "AT&V"
    status, response = self._send_atcmd(cmd, 18)
    return status, response
  
  def at_cfun(self, radio_on=False):
    cmd = "AT+CFUN=1" if radio_on else "AT+CFUN=0"
    if not self._send_atcmd(cmd, DEFAULT_TIMEOUT):
      return False
    if radio_on:
      urcs = ["+CPIN: READY", "+QUSIM: 1", "+QIND: SMS DONE"]
      for urc in urcs:
        if not self._wait_for_urc(urc, timeout=10):
          return False
    return True

  def at_creg(self):
    cmd = "AT+CREG?"
    connection_status = 1
    status, response = self._send_atcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(f"response = {response}")
      connection_status = int(response.split(",")[1][:1])
      logging.debug(f"connection status = {connection_status}")
      return status, connection_status

    return False, None

  def at_csq(self):
    cmd = "AT+CSQ"
    status, response = self._send_atcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      signal_quality = int(response.split(":")[1].split(",")[0])
      logging.debug(f"signal quality = {signal_quality}")
      return status, signal_quality

    return False, None
  
if __name__ == "__main__":
    my_bg95_cmd = Bg95_cmd()

    print("\n>>>>>>")
    if not my_bg95_cmd.connect():
      print("FAILED TO OPEN USB CONNECTION")
      exit()

    print("\n>>>>>>")
    status = my_bg95_cmd.at()
    if status:
      print("COMMAND 'AT' PASSED!")

    # print("\n>>>>>>")
    # status, response = my_bg95_cmd.ati()
    # if status:
    #   print("COMMAND 'ATI' PASSED!")
    #   print(response)

    # print("\n>>>>>>")
    # status, response = my_bg95_cmd.at_gsn()
    # if status:
    #   print("COMMAND 'AT+GSN' PASSED!")
    #   print(response)

    # print("\n>>>>>>")
    # status, response = my_bg95_cmd.at_v()
    # if status:
    #   print("COMMAND 'AT&V' PASSED!")
    #   print(response)

    print("\n>>>>>>")
    status = my_bg95_cmd.at_cfun(0)
    if status:
      print("COMMAND 'AT+CFUN=0' PASSED!")

    print("\n>>>>>>")
    status = my_bg95_cmd.at_cfun(1)
    if status:
      print("COMMAND 'AT+CFUN=1' PASSED!")

    print("\n>>>>>>") 
    response = 0
    while response != 1:
      status, response = my_bg95_cmd.at_creg()
      time.sleep(.1)
    if status:
      print(f"COMMAND 'AT+CREG' successfully returned {response}")

    time.sleep(5)
    print("\n>>>>>>")
    NO_SIGNAL = 99
    response = NO_SIGNAL
    while response == NO_SIGNAL:
      status, response = my_bg95_cmd.at_csq()
      time.sleep(0.1)    
    if status:
      print(f"COMMAND 'AT+CSQ' successfully returned {response}!")

    print("\n>>>>>>")
    my_bg95_cmd.close()
