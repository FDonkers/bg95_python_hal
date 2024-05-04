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
  _port = 'COM11'
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
  _RESPONSES = ["OK", "ERROR", "+CME ERROR:"]
  
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
    status, cmd, response = self._read_line(timeout)
    if status:
      return response == self._RESPONSE_OK
    else:
      return False

  def _send_ATcmd(self, cmd="", timeout=DEFAULT_TIMEOUT):
    logging.debug("\n>>>>>>")
    logging.debug(f"sending {cmd}")
    if not self._write_line(cmd):
      logging.error(f"not able to send {cmd}")
      return False, None

    if not self._read_echo(timeout):
      logging.error(f"did not receive echo for {cmd}")
      return False, None

    # collect response
    line = ""
    response = ""
    found = False

    while not found:
      status, line = self._read_reponse(timeout)
      if status:
        response += '< ' + line + "\n"
        if any(line.startswith(res) for res in self._RESPONSES):
          found = True
      else:
        logging.error(f"unexpected response for {cmd}")
        return False, None

    if line.startswith(self._RESPONSES[0]):
      return True, response
    else:
      logging.error(f"did not receive 'OK' for {cmd}")
      return False, response

  def _wait_for_urc(self, urc="", timeout=DEFAULT_TIMEOUT):
    # collect all responses until given URC is found
    response = ""
    while True:
      status, line = self._read_reponse(timeout)
      logging.debug(line)
      if status:
        response += '< ' + line + "\n"
        if line.startswith(urc):
          return True, response
      else:
        logging.error(f"incorrect response for {urc}")
        return False

  def AT(self):
    # Generic AT command to check if modem is alive
    cmd = "AT"
    status, response = self._send_ATcmd(cmd, 0)
    return status, cmd, response

  def ATE(self, echo_on=True):
    # Set echo on or off
    cmd = "ATE1" if echo_on else "ATE0"
    status, response = self._send_ATcmd(cmd, 0)
    return status, cmd, response

  def ATI(self):
    # Request product identification information
    cmd = "ATI"
    status, response = self._send_ATcmd(cmd, 4)
    return status, cmd, response

  def AT_GSN(self):
    # Request product serial number identification (IMEI  number)
    cmd = "AT+GSN"
    status, response = self._send_ATcmd(cmd, 2)
    return status, cmd, response

  def AT_V(self):
    # Request current configuration
    cmd = "AT&V"
    status, response = self._send_ATcmd(cmd, 18)
    return status, cmd, response
  
  def AT_CFUN(self, radio_on=False):
    # Set radio on or off
    cmd = "AT+CFUN=1" if radio_on else "AT+CFUN=0"
    if not self._send_ATcmd(cmd, DEFAULT_TIMEOUT):
      return False, cmd
    if radio_on:
      urcs = ["+CPIN: READY", "+QUSIM: 1", "+QIND: SMS DONE"]
      for urc in urcs:
        if not self._wait_for_urc(urc, timeout=10):
          return False, cmd
    return True, cmd

  def AT_CREG(self):
    # Request GSM network registration status
    cmd = "AT+CREG?"
    connection_status = 1
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(f"response = {response}")
      connection_status = int(response.split(",")[1][:1])
      logging.debug(f"connection status = {connection_status}")
      return status, cmd, connection_status

    return False, cmd, None

  def AT_CEREG(self):
    # Request LTE network registration status
    cmd = "AT+CEREG?"
    connection_status = 1
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(f"response = {response}")
      connection_status = int(response.split(",")[1][:1])
      logging.debug(f"connection status = {connection_status}")
      return status, cmd, connection_status

    return False, cmd, None

  def AT_CSQ(self):
    # Request signal quality (RSSI)
    cmd = "AT+CSQ"
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      signal_quality = int(response.split(":")[1].split(",")[0])
      logging.debug(f"signal quality = {signal_quality}")
      return status, cmd, signal_quality

    return False, cmd, None

  def AT_CGATT_REQUEST(self):
    # Request GPRS attach status
    cmd = "AT+CGATT?"
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      return status, cmd, response

    return False, cmd, None
  
  def AT_CGEREP_REQUEST(self):
    # Request GPRS event reporting
    # NOTE: only call when CFUN=1, otherwise an error will be returned
    cmd = "AT+CGEREP?"
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      return status, cmd, response

    return False, cmd, None

  def AT_CGPADDR_REQUEST(self):
    # Request PDP IP address
    cmd = "AT+CGPADDR=" + str(self._CID)
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      return status, cmd, response

    return False, cmd, None

  def AT_CGDCONT_REQUEST(self):
    # Request PDP context
    cmd = "AT+CGDCONT?"
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      return status, cmd, response

    return False, None
  
  def AT_CCLK_REQUEST(self):
    # Request PDP context
    cmd = "AT+CCLK?"
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      return status, cmd, response

    return False, None
  
  #ToDo: add more commands
  
############################################################################################################
# QUECTEL MISC FUNCTIONS
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
        return status, cmd, response
    return False, cmd, None

  def AT_QNTP(self):
    # request time from NTP server
    cmd = 'AT+QNTP=1,"nl.pool.ntp.org",123' # google DNS
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      # also collect multiple URC responses
      status, response = self._wait_for_urc("+QNTP:", DEFAULT_TIMEOUT)
      if status:
        logging.debug(response)
        return status, cmd, response
    return False, cmd, None

############################################################################################################
# QUECTEL GNSS FUNCTIONS
############################################################################################################

  GNSS_ERROR_CODES =  {
    501: "Invalid parameter",
    502: "Operation not supported",
    503: "GNSS subsystem busy",
    504: "Session is ongoing",
    505: "Session not active",
    506: "Operation timeout",
    507: "Function not enabled",
    508: "Time information error",
    509: "XTRA not enabled",
    512: "Validity time is out of range",
    513: "Internal resource error",
    514: "GNSS locked",
    515: "End by E911",
    516: "No fix",
    517: "Geo-fence ID does not exist",
    518: "Sync time failed",
    519: "XTRA file does not exist",
    520: "XTRA file on downloading",
    521: "XTRA file is valid",
    522: "GNSS is working",
    523: "Time injection error",
    524: "XTRA file is invalid",
    549: "Unknown error"
  }

  def extract_urc(response, urc): 
    # extract URC response
    for line in response.split("\n"):
      if line.startswith('< '+urc):
        r = line.split(":")[1].strip()
        return True, r
    return False, None

  def AT_QGPSCFG_PRIO(self, gnss_prio=1):
    # set GNSS priority to 0 (GNSS) or 1 (WWAN)
    cmd = f'AT+QGPSCFG="priority",{gnss_prio},0'
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_QGPS_ON(self):
    # switch GNSS ON
    cmd = f'AT+QGPS=1,1'
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_QGPS_END(self):
    # switch GNSS OFF
    cmd = f'AT+QGPSEND'
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_QGPS_STATUS_REQUEST(self):
    # query GNSS ON/OFF status
    cmd = f'AT+QGPS?'
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_QGPSLOC_REQUEST(self):
    # query GNSS location
    cmd = f'AT+QGPSLOC?'
    status, response = self._send_ATcmd(cmd, DEFAULT_TIMEOUT)
    if status:
      logging.debug(response)
      return status, cmd, response
    return False, cmd, response


############################################################################################################
# MISC SUPPORT FUNCTIONS
############################################################################################################

def modem_run_general_at_commands():
  status = my_Bg95.AT()
  if status:
    logging.info(f"PASSED!")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_Bg95.ATI()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_Bg95.ATE(True)
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_Bg95.AT_GSN()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_Bg95.AT_CCLK_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  # status, cmd, response = my_Bg95.AT_V()
  # if status:
    # logging.info(f"{cmd} PASSED! with response:\n{response}")
  # else:
  #   logging.info(f"{cmd} FAILED!")
  #   return False

  return True

def modem_connect_to_network():
  status, cmd = my_Bg95.AT_CFUN(0)
  if status:
    logging.info(f"{cmd} PASSED!")

  status, cmd = my_Bg95.AT_CFUN(1)
  if status:
    logging.info(f"{cmd} PASSED!")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_Bg95.AT_CGEREP_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  response = 0
  while response != 1:
    status, cmd, response = my_Bg95.AT_CREG()
    time.sleep(.1)
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_Bg95.AT_CGATT_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  NO_SIGNAL = 99
  response = NO_SIGNAL
  while response == NO_SIGNAL:
    status, cmd, response = my_Bg95.AT_CSQ()
    time.sleep(.1)    
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_Bg95.AT_CGDCONT_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_Bg95.AT_CGPADDR_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_Bg95.AT_CGEREP_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  return True

def modem_run_GNSS_commands():
  # set priority to GNSS
  status, cmd, response = my_Bg95.AT_QGPSCFG_PRIO(gnss_prio=0)
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  # check if GNSS is already ON
  status, cmd, response = my_Bg95.AT_QGPS_STATUS_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
    status, urc = Bg95_ATcmds.extract_urc(response, "+QGPS")
    gps_on = (urc[0] == '1')
    logging.info(f"GPS is ON") if (gps_on == True) else logging.info(f"GPS is OFF")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  # switch ON GNSS if not already ON  
  if not gps_on:
    status, cmd, response = my_Bg95.AT_QGPS_ON()
    if status:
      logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

  # check if GNSS is indeed switched ON
  status, cmd, response = my_Bg95.AT_QGPS_STATUS_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
    status, urc = Bg95_ATcmds.extract_urc(response, "+QGPS")
    gps_on = (urc[0] == '1')
    logging.info(f"GPS is ON") if (gps_on == True) else logging.info(f"GPS is OFF")
  else:
    logging.error(f"{cmd} FAILED!")
    return False
  if not gps_on:
    logging.error(f"GPS is still OFF")
    return False

  # get GPS location
  got_fix = False
  while not got_fix:
    time.sleep(1)
    status, cmd, response = my_Bg95.AT_QGPSLOC_REQUEST()
    if status:
      # check if fix is obtained
      s, urc = Bg95_ATcmds.extract_urc(response, "+CME ERROR")
      got_fix = (urc == None)

  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
    status, res = Bg95_ATcmds.extract_urc(response, "+QGPSLOC")
    logging.info(f"GPS response = {res}")
    r = res.split(",")
    logging.info(f"Timestamp = {r[0]}")
    logging.info(f"Latitude  = {r[1]}")
    logging.info(f"Longitude = {r[2]}\n")
  else:
    logging.info(f"{cmd} FAILED!")
    logging.info(f"returned {response}")
    return False

  # switch OFF GNSS
  status, cmd, response = my_Bg95.AT_QGPS_END()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  # set priority to WWAN
  status, cmd, response = my_Bg95.AT_QGPSCFG_PRIO(gnss_prio=1)
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

def modem_run_IP_commands():
  status, cmd, response = my_Bg95.AT_QPING()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_Bg95.AT_QNTP()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  return True

def modem_disconnect_from_network():
  status, cmd = my_Bg95.AT_CFUN(0)
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

    # modem_run_general_at_commands()

    modem_run_GNSS_commands()
  
    # ##### START TIMER
    # t_start = time.time()

    # modem_connect_to_network()


    # ##### READ TIMER
    # t_stop = time.time()
    # logging.info(f"Time taken: {t_stop - t_start}\n")

    # modem_run_IP_commands()

    # modem_disconnect_from_network()
    
    # ##### READ TIMER
    # t_stop = time.time()
    # logging.info(f"Time taken: {t_stop - t_start}\n")

    my_Bg95.close_usb()

    logging.debug("\n******************************")
