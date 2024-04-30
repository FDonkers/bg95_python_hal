import time
import serial
import logging
# https://realpython.com/python-logging/ ; levels are DEBUG, INFO, WARNING, ERROR, CRITICAL
logging.basicConfig(format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

DEFAULT_TIMEOUT = 1

############################################################################################################
# class Bg95_serial
############################################################################################################

class Bg95_serial:
  _port = 'COM7'
  _baudrate = 115200
  _ser = None
  _connected = False

  def __init__(self):
    pass

  def open_usb(self):
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

  def close_usb(self):
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

############################################################################################################
# class Bg95_ATcmds: GENERAL 3GPP AT COMMANDS
############################################################################################################

class Bg95_ATcmds (Bg95_serial):
  _RESPONSE_OK = "OK"
  _RESPONSE_NOK = "ERROR"
  _CID = 1
  _PDP_TYPE = "IPV4V6"
  _APN_OPENINTERNET = "internet.m2m"
  _APN_KNPTHINGS = "kpnthings.m2m"

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

  def _send_ATcmd(self, cmd="", timeout=DEFAULT_TIMEOUT):
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
    # collect all responses until given URC is found
    response = ""
    while True:
      status, line = self._read_reponse(timeout)
      logging.debug(line)
      if status:
        response += '< ' + line + "\n"
        if urc in line:
          return True, response
      else:
        logging.error(f"incomplete response for {urc}")
        return False

  def AT(self):
    # Generic AT command to check if modem is alive
    cmd = "AT"
    status, response = self._send_ATcmd(cmd, 0)
    return status, response

  def ATE(self, echo_on=True):
    # Set echo on or off
    cmd = "ATE1" if echo_on else "ATE0"
    status, response = self._send_ATcmd(cmd, 0)
    return status, response

  def ATI(self):
    # Request product identification information
    cmd = "ATI"
    status, response = self._send_ATcmd(cmd, 4)
    return status, response

  def AT_GSN(self):
    # Request product serial number identification (IMEI  number)
    cmd = "AT+GSN"
    status, response = self._send_ATcmd(cmd, 2)
    return status, response

  def AT_V(self):
    # Request current configuration
    cmd = "AT&V"
    status, response = self._send_ATcmd(cmd, 18)
    return status, response
  
  def AT_CFUN(self, radio_on=False):
    # Set radio on or off
    cmd = "AT+CFUN=1" if radio_on else "AT+CFUN=0"
    if not self._send_ATcmd(cmd, DEFAULT_TIMEOUT):
      return False
    if radio_on:
      urcs = ["+CPIN: READY", "+QUSIM: 1", "+QIND: SMS DONE"]
      for urc in urcs:
        if not self._wait_for_urc(urc, timeout=10):
          return False
    return True

  def AT_CREG(self):
    # Request network registration status
    cmd = "AT+CREG?"
    connection_status = 1
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(f"response = {response}")
      connection_status = int(response.split(",")[1][:1])
      logging.debug(f"connection status = {connection_status}")
      return status, connection_status

    return False, None

  def AT_CSQ(self):
    # Request signal quality (RSSI)
    cmd = "AT+CSQ"
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      signal_quality = int(response.split(":")[1].split(",")[0])
      logging.debug(f"signal quality = {signal_quality}")
      return status, signal_quality

    return False, None

  def AT_CGATT_REQUEST(self):
    # Request GPRS attach status
    cmd = "AT+CGATT?"
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      return status, response

    return False, None
  
  def AT_CGEREP_REQUEST(self):
    # Request GPRS event reporting
    # NOTE: only call when CFUN=1, otherwise an error will be returned
    cmd = "AT+CGEREP?"
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      return status, response

    return False, None

  def AT_CGPADDR_REQUEST(self):
    # Request PDP IP address
    cmd = "AT+CGPADDR=" + str(self._CID)
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      return status, response

    return False, None

  def AT_CGDCONT_REQUEST(self):
    # Request PDP context
    cmd = "AT+CGDCONT?"
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      return status, response

    return False, None
  
  def AT_CCLK_REQUEST(self):
    # Request PDP context
    cmd = "AT+CCLK?"
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      return status, response

    return False, None
  
  #ToDo: add more commands
  
############################################################################################################
# QUECTEL SPECIFIC FUNCTIONS
############################################################################################################

  def AT_QPING(self):
    # ping an IP address
    # cmd = 'AT+QPING=1,"45.82.191.174"' # www.felixdonkers.nl
    cmd = 'AT+QPING=1,"8.8.8.8"' # google DNS
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      # also collect multiple URC responses
      status, response = self._wait_for_urc("+QPING: 0,4", DEFAULT_TIMEOUT)
      if status:
        logging.debug(response)
        return status, response
    return False, None

  def AT_QNTP(self):
    # request time from NTP server
    cmd = 'AT+QNTP=1,"nl.pool.ntp.org"' # google DNS
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      # also collect multiple URC responses
      status, response = self._wait_for_urc("+QNTP:", DEFAULT_TIMEOUT)
      if status:
        logging.debug(response)
        return status, response
    return False, None

############################################################################################################
# MISC SUPPORT FUNCTIONS
############################################################################################################

def modem_run_general_at_commands():
  logging.debug("\n>>>>>>")
  cmd = "COMMAND 'AT'"
  status = my_Bg95.AT()
  if status:
    logging.info(f"{cmd} PASSED!")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  logging.debug("\n>>>>>>")
  cmd = "COMMAND 'ATI'"
  status, response = my_Bg95.ATI()
  if status:
    logging.info(f"{cmd} PASSED!")
    logging.info(response)
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  logging.debug("\n>>>>>>")
  cmd = "COMMAND 'ATE'"
  status, response = my_Bg95.ATE(True)
  if status:
    logging.info(f"{cmd} PASSED!")
    logging.info(response)
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  logging.debug("\n>>>>>>")
  cmd = "COMMAND 'AT+GSN'"
  status, response = my_Bg95.AT_GSN()
  if status:
    logging.info(f"{cmd} PASSED!")
    logging.info(response)
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  logging.debug("\n>>>>>>")
  cmd = "COMMAND 'AT+CCLK?'"
  status, response = my_Bg95.AT_CCLK_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED!")
    logging.info(response)
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  # logging.debug("\n>>>>>>")
  # cmd = "COMMAND 'AT&V'"
  # status, response = my_Bg95.AT_V()
  # if status:
  #   print(f"{cmd} PASSED!")
  #   print(response)
  # else:
  #   logging.info(f"{cmd} FAILED!")
  #   return False

  return True

def modem_connect_to_network():
    logging.debug("\n>>>>>>")
    status = my_Bg95.AT_CFUN(0)
    if status:
      logging.info("COMMAND 'AT+CFUN=0' PASSED!")

    logging.debug("\n>>>>>>")
    cmd = "COMMAND 'AT+CFUN=1'"
    status = my_Bg95.AT_CFUN(1)
    if status:
      logging.info(f"{cmd} PASSED!")
    else:
      logging.info(f"{cmd} FAILED!")
      return False

    logging.debug("\n>>>>>>")
    cmd = "COMMAND 'AT+CGEREP?"
    status, response = my_Bg95.AT_CGEREP_REQUEST()
    if status:
      logging.info(f"{cmd} PASSED!")
      logging.info(response)
    else:
      logging.info(f"{cmd} FAILED!")
      return False

    logging.debug("\n>>>>>>")
    cmd = "COMMAND 'AT+CREG'"
    response = 0
    while response != 1:
      status, response = my_Bg95.AT_CREG()
      time.sleep(.1)
    if status:
      logging.info(f"{cmd} successfully returned {response}")
    else:
      logging.info(f"{cmd} FAILED!")
      return False

    logging.debug("\n>>>>>>")
    cmd = "COMMAND 'AT+CGATT?'"
    status, response = my_Bg95.AT_CGATT_REQUEST()
    if status:
      logging.info(f"{cmd} successfully returned {response}")
    else:
      logging.info(f"{cmd} FAILED!")
      return False

    logging.debug("\n>>>>>>")
    cmd = "COMMAND 'AT+CSQ'"
    NO_SIGNAL = 99
    response = NO_SIGNAL
    while response == NO_SIGNAL:
      status, response = my_Bg95.AT_CSQ()
      time.sleep(.1)    
    if status:
      logging.info(f"{cmd} successfully returned {response}")
    else:
      logging.info(f"{cmd} FAILED!")
      return False

    logging.debug("\n>>>>>>")
    cmd = "COMMAND 'AT+CGDCONT?'"
    status, response = my_Bg95.AT_CGDCONT_REQUEST()
    if status:
      logging.info(f"{cmd} successfully returned {response}")
    else:
      logging.info(f"{cmd} FAILED!")
      return False

    logging.debug("\n>>>>>>")
    cmd = "COMMAND 'AT+CGPADDR=" + str(my_Bg95._CID) + "'"
    status, response = my_Bg95.AT_CGPADDR_REQUEST()
    if status:
      logging.info(f"{cmd} successfully returned {response}")
    else:
      logging.info(f"{cmd} FAILED!")
      return False

    logging.debug("\n>>>>>>")
    cmd = "COMMAND 'AT+CGEREP?"
    status, response = my_Bg95.AT_CGEREP_REQUEST()
    if status:
      logging.info(f"{cmd} PASSED!")
      logging.info(response)
    else:
      logging.info(f"{cmd} FAILED!")
      return False

    return True

def modem_run_IP_commands():
    logging.debug("\n>>>>>>")
    cmd = "COMMAND 'AT+QPING'"
    status, response = my_Bg95.AT_QPING()
    if status:
      logging.info(f"{cmd} PASSED!")
      logging.info(f"{cmd} successfully returned {response}")
    else:
      logging.info(f"{cmd} FAILED!")
      return False

    logging.debug("\n>>>>>>")
    cmd = "COMMAND 'AT+QNTP'"
    status, response = my_Bg95.AT_QNTP()
    if status:
      logging.info(f"{cmd} PASSED!")
      logging.info(f"{cmd} successfully returned {response}")
    else:
      logging.info(f"{cmd} FAILED!")
      return False

    return True

def modem_disconnect_from_network():
    logging.debug("\n>>>>>>")
    cmd = "COMMAND 'AT+CFUN=0'"
    status = my_Bg95.AT_CFUN(0)
    if status:
      logging.info(f"{cmd} PASSED!")
    else:
      logging.info(f"{cmd} FAILED!")
      return False

    return True

############################################################################################################
# MAIN
############################################################################################################

  
if __name__ == "__main__":
    my_Bg95 = Bg95_ATcmds()

    logging.debug("\n******************************")

    if not my_Bg95.open_usb():
      print("FAILED TO OPEN USB CONNECTION")
      exit()

    modem_run_general_at_commands()

    ##### START TIMER
    t_start = time.time()

    modem_connect_to_network()


    ##### READ TIMER
    t_stop = time.time()
    logging.info(f"Time taken: {t_stop - t_start}\n")

    modem_run_IP_commands()

    modem_disconnect_from_network()
    
    ##### READ TIMER
    t_stop = time.time()
    logging.info(f"Time taken: {t_stop - t_start}\n")

    my_Bg95.close_usb()

    logging.debug("\n******************************")
