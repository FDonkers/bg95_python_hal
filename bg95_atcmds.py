import time
import logging
import serial
from bg95_serial import bg95_serial

############################################################################################################
# class Bg95_ATcmds: GENERAL 3GPP AT COMMANDS
############################################################################################################

class bg95_atcmds (bg95_serial, ):
  _RESPONSES = ["OK", "ERROR", "+CME ERROR:"]
  
  _CID = 1
  _PDP_TYPE = "IPV4V6"
  _APN_OPENINTERNET = "internet.m2m"
  _APN_KNPTHINGS = "kpnthings.m2m"
  _DEFAULT_TIMEOUT = 1
  _my_logger = None

  def __init__(self, log_handle=None):
    self._my_logger = log_handle
    super().__init__(log_handle=self._my_logger, default_timeout = self._DEFAULT_TIMEOUT)
    pass

  def _read_echo(self, timeout=_DEFAULT_TIMEOUT):
    # ToDo: check echo response
    return self._read_line(timeout)

  def _read_reponse(self, timeout=_DEFAULT_TIMEOUT):
    return self._read_line()

  def _read_ok(self, timeout=_DEFAULT_TIMEOUT):
    status, cmd, response = self._read_line(timeout)
    if status:
      return response == self._RESPONSE_OK
    else:
      return False

  def _send_ATcmd(self, cmd="", timeout=_DEFAULT_TIMEOUT):
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

  def _wait_for_urc(self, urc="", timeout=_DEFAULT_TIMEOUT):
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
    if not self._send_ATcmd(cmd):
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
    status, response = self._send_ATcmd(cmd)
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
    status, response = self._send_ATcmd(cmd)
    if status:
      logging.debug(f"response = {response}")
      connection_status = int(response.split(",")[1][:1])
      logging.debug(f"connection status = {connection_status}")
      return status, cmd, connection_status

    return False, cmd, None

  def AT_CSQ(self):
    # Request signal quality (RSSI)
    cmd = "AT+CSQ"
    status, response = self._send_ATcmd(cmd)
    if status:
      logging.debug(response)
      signal_quality = int(response.split(":")[1].split(",")[0])
      logging.debug(f"signal quality = {signal_quality}")
      return status, cmd, signal_quality

    return False, cmd, None

  def AT_CGATT_REQUEST(self):
    # Request GPRS attach status
    cmd = "AT+CGATT?"
    status, response = self._send_ATcmd(cmd)
    if status:
      logging.debug(response)
      return status, cmd, response

    return False, cmd, None
  
  def AT_CGEREP_REQUEST(self):
    # Request GPRS event reporting
    # NOTE: only call when CFUN=1, otherwise an error will be returned
    cmd = "AT+CGEREP?"
    status, response = self._send_ATcmd(cmd)
    if status:
      logging.debug(response)
      return status, cmd, response

    return False, cmd, None

  def AT_CGPADDR_REQUEST(self):
    # Request PDP IP address
    cmd = "AT+CGPADDR=" + str(self._CID)
    status, response = self._send_ATcmd(cmd)
    if status:
      logging.debug(response)
      return status, cmd, response

    return False, cmd, None

  def AT_CGDCONT_REQUEST(self):
    # Request PDP context
    cmd = "AT+CGDCONT?"
    status, response = self._send_ATcmd(cmd)
    if status:
      logging.debug(response)
      return status, cmd, response

    return False, None
  
  def AT_CCLK_REQUEST(self):
    # Request PDP context
    cmd = "AT+CCLK?"
    status, response = self._send_ATcmd(cmd)
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
    status, response = self._send_ATcmd(cmd)
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
    status, response = self._send_ATcmd(cmd)
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
    status, response = self._send_ATcmd(cmd)
    if status:
      logging.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_QGPS_ON(self):
    # switch GNSS ON
    cmd = f'AT+QGPS=1,1'
    status, response = self._send_ATcmd(cmd)
    if status:
      logging.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_QGPS_END(self):
    # switch GNSS OFF
    cmd = f'AT+QGPSEND'
    status, response = self._send_ATcmd(cmd)
    if status:
      logging.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_QGPS_STATUS_REQUEST(self):
    # query GNSS ON/OFF status
    cmd = f'AT+QGPS?'
    status, response = self._send_ATcmd(cmd)
    if status:
      logging.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_QGPSLOC_REQUEST(self):
    # query GNSS location
    cmd = f'AT+QGPSLOC?'
    status, response = self._send_ATcmd(cmd)
    if status:
      logging.debug(response)
      return status, cmd, response
    return False, cmd, response


############################################################################################################
# QUECTEL HTTP(S) FUNCTIONS
############################################################################################################

  HTTPS_ERROR = {
      0: "Operation_successful",
    701: "HTTP(S) unknown error",
    702: "HTTP(S) timeout",
    703: "HTTP(S) busy",
    704: "HTTP(S) UART busy",
    705: "HTTP(S) no GET/POST/PUT requests",
    706: "HTTP(S) network busy",
    707: "HTTP(S) network open failed",
    708: "HTTP(S) network no configuration",
    709: "HTTP(S) network deactivated",
    710: "HTTP(S) network error",
    711: "HTTP(S) URL error",
    712: "HTTP(S) empty URL",
    713: "HTTP(S) IP address error",
    714: "HTTP(S) DNS error",
    715: "HTTP(S) socket create error",
    716: "HTTP(S) socket connect error",
    717: "HTTP(S) socket read error",
    718: "HTTP(S) socket write error",
    719: "HTTP(S) socket closed",
    720: "HTTP(S) data encode error",
    721: "HTTP(S) data decode error",
    722: "HTTP(S) read timeout",
    723: "HTTP(S) response failed",
    724: "Incoming call busy",
    725: "Voice call busy",
    726: "Input timeout",
    727: "Wait data timeout",
    728: "Wait HTTP(S) response timeout",
    729: "Memory allocation failed",
    730: "Invalid parameter"
  }                          

  def AT_QHTTPCFG(self):
    # query IP address
    cmd = f'AT+QHTTPCFG?'
    status, response = self._send_ATcmd(cmd)
    if status:
      logging.debug(response)
      return status, cmd, response
    return False, cmd, response

  def AT_QIACT(self):
    # query IP address
    cmd = f'AT+QIACT?'
    status, response = self._send_ATcmd(cmd)
    if status:
      logging.debug(response)
      return status, cmd, response
    return False, cmd, response
