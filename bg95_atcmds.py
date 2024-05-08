from bg95_serial import bg95_serial

############################################################################################################
# class bg95_atcmds: 3GPP AT COMMANDS
############################################################################################################

class bg95_atcmds (bg95_serial):
  _RESPONSE_OK = "OK"
  _RESPONSE_CONNECT = "CONNECT"
  _RESPONSE_ERROR = "ERROR"
  _RESPONSE_CME_ERROR = "+CME ERROR:"
  _RESPONSES_OK = (_RESPONSE_OK, _RESPONSE_CONNECT)
  _RESPONSES_NOK = (_RESPONSE_ERROR, _RESPONSE_CME_ERROR)
  _RESPONSES = _RESPONSES_OK + _RESPONSES_NOK
  
  _CID = 1
  _PDP_TYPE = "IPV4V6"
  _APN_OPENINTERNET = "internet.m2m"
  _APN_KNPTHINGS = "kpnthings.m2m"
  _DEFAULT_TIMEOUT = 5  #seconds
  _my_logger = None

  def __init__(self, logger=None):
    self._my_logger = logger
    super().__init__(log_handle=self._my_logger, default_timeout = self._DEFAULT_TIMEOUT)
    pass

############################################################################################################
# BASIC AT CMD FUNCTIONS
############################################################################################################

  def _AT_send_cmd(self, cmd="", timeout=_DEFAULT_TIMEOUT):
    self._my_logger.info(">>>>>>")
    self._my_logger.info(f"sending {cmd}")
    if not self._write_line(cmd):
      self._my_logger.error(f"not able to send {cmd}")
      return False, None
    # assume echo enabled (ATE), so read back command
    if not self._read_line(timeout):
      self._my_logger.error(f"did not receive echo for {cmd}")
      return False, None

    # collect response
    response = ""
    while True:
      status, line = self._read_line(timeout)
      if status:
        if (len(line) > 0):
          response += line + "\n"
        if line.startswith(self._RESPONSES_OK):
          self._my_logger.debug(f"response for {cmd} = {response}")
          return True, response
        elif line.startswith(self._RESPONSES_NOK): 
          self._my_logger.error(f"response for {cmd} = {response}")
          return False, response
      else:
        self._my_logger.error(f"unexpected status for {cmd}")
        return False, None

  def _AT_send_payload(self, payload="", timeout=_DEFAULT_TIMEOUT):
    response = ""
    status = self._write_line(payload)
    while True:
      status, line = self._read_line(timeout)
      if status:
        if (len(line) > 0):
          response += line + "\n"
        if line.startswith(self._RESPONSES_OK):
          return True, response
      else:
        self._my_logger.error(f"unexpected status for 'send_payload'")
        return False, None
      
  def _AT_receive_payload(self, timeout=_DEFAULT_TIMEOUT):
    response = ""
    while True:
      status, line = self._read_line(timeout)
      if status:
        if (len(line) > 0):
          response += line + "\n"
        if line.startswith(self._RESPONSES_OK):
          return True, response
      else:
        self._my_logger.error(f"unexpected status for 'receive_payload'")
        return False, None

  def _AT_wait_for_urc(self, urc="", timeout=_DEFAULT_TIMEOUT):
    # collect all responses until given URC is found
    response = ""
    while True:
      status, line = self._read_line(timeout)
      if status:
        if (len(line) > 0):
          response += line + "\n"
        if line.startswith(urc):
          return True, response
      else:
        self._my_logger.error(f"incorrect response for {urc}")
        return False

############################################################################################################
# QUECTEL GENERAL COMMANDS
############################################################################################################

  def AT(self):
    # Generic AT command to check if modem is alive
    cmd = "AT"
    status, response = self._AT_send_cmd(cmd)
    return status, cmd, response

  def ATI(self):
    # Request product identification information
    cmd = "ATI"
    status, response = self._AT_send_cmd(cmd)
    return status, cmd, response

  def AT_GSN(self):
    # Request product serial number identification (IMEI  number)
    cmd = "AT+GSN"
    status, response = self._AT_send_cmd(cmd)
    return status, cmd, response

  def AT_V(self):
    # Request current configuration
    cmd = "AT&V"
    status, response = self._AT_send_cmd(cmd)
    return status, cmd, response

  def ATE(self, echo_on=True):
    # Set echo on or off
    cmd = "ATE1" if echo_on else "ATE0"
    status, response = self._AT_send_cmd(cmd)
    return status, cmd, response
  
  def AT_CFUN(self, radio_on=False):
    # Set radio on or off
    cmd = "AT+CFUN=1" if radio_on else "AT+CFUN=0"
    if not self._AT_send_cmd(cmd):
      return False, cmd
    if radio_on:
      urcs = ["+CPIN: READY", "+QUSIM: 1", "+QIND: SMS DONE"]
      for urc in urcs:
        if not self._AT_wait_for_urc(urc, timeout=10):
          return False, cmd
    return True, cmd

############################################################################################################
# QUECTEL SERIAL INTERFACE CONTROL COMMANDS
############################################################################################################
#TBD

############################################################################################################
# QUECTEL (U)SIM RELATED COMMANDS
############################################################################################################

  def AT_CIMI_REQUEST(self):
    # Request SIMs IMSI number, note: only valid after CFUN=1
    cmd = "AT+CIMI"
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_QCCID_REQUEST(self):
    # Request SIMs CCID number, note: only valid after CFUN=1
    cmd = "AT+QCCID"
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, None

############################################################################################################
# QUECTEL NETWORK SERVICE COMMANDS
############################################################################################################

  def AT_CREG(self):
    # Request GSM network registration status
    cmd = "AT+CREG?"
    connection_status = 1
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(f"response = {response}")
      connection_status = int(response.split(",")[1][:1])
      self._my_logger.debug(f"connection status = {connection_status}")
      return status, cmd, connection_status
    return False, cmd, None

  def AT_COPS_REQUEST(self):
    # Request current operator
    cmd = "AT+COPS?"
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_CSQ(self):
    # Request signal quality (RSSI)
    cmd = "AT+CSQ"
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      signal_quality = int(response.split(":")[1].split(",")[0])
      self._my_logger.debug(f"signal quality = {signal_quality}")
      return status, cmd, signal_quality
    return False, cmd, None

  def AT_QNWINFO(self):
    # Request network information
    cmd = "AT+QNWINFO"
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_QCSQ(self):
    # Request network information
    cmd = "AT+QCSQ"
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, None
  
############################################################################################################
# QUECTEL SMS COMMANDS
############################################################################################################

############################################################################################################
# QUECTEL PACKET DOMAIN COMMANDS
############################################################################################################

  def AT_CGATT_REQUEST(self):
    # Request Packet Domain Service (PS) attach status
    cmd = "AT+CGATT?"
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, None
  
  def AT_CGDCONT_REQUEST(self):
    # Request PDP context
    cmd = "AT+CGDCONT?"
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, None
  
  def AT_CGACT_REQUEST(self):
    # Request PDP context
    cmd = "AT+CGACT?"
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, None

  def AT_CGPADDR_REQUEST(self):
    # Request PDP IP address
    cmd = "AT+CGPADDR=" + str(self._CID)
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_CGREG_REQUEST(self):
    # Request EGPRS network registration status
    # NOTE: only call when CFUN=1, otherwise an error will be returned
    cmd = "AT+CGREG?"
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_CGEREP_REQUEST(self):
    # Request Packet Domain event reporting
    # NOTE: only call when CFUN=1, otherwise an error will be returned
    cmd = "AT+CGEREP?"
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_CEREG(self):
    # Request LTE network registration status
    cmd = "AT+CEREG?"
    connection_status = 1
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(f"response = {response}")
      connection_status = int(response.split(",")[1][:1])
      self._my_logger.debug(f"connection status = {connection_status}")
      return status, cmd, connection_status
    return False, cmd, None

  
############################################################################################################
# QUECTEL HARDWARE RELATED FUNCTIONS
############################################################################################################

  def AT_POWERDOWN(self):
    # Modem power down, 0=immediate, 1=normal mode
    cmd = "AT+POWD=1"
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
  #ToDo: wait for "POWERED DOWN" URC
    return False, cmd, None
  
  def AT_CCLK_REQUEST(self):
    # Request PDP context
    cmd = "AT+CCLK?"
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, None
  
  def AT_QTEMP(self):
    # request silicon temperatures
    cmd = 'AT+QTEMP'
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, None

############################################################################################################
# QUECTEL TCPIP FUNCTIONS
############################################################################################################

  def AT_QPING(self):
    # ping an IP address
    # cmd = 'AT+QPING=1,"45.82.191.174"' # www.felixdonkers.nl
    cmd = 'AT+QPING=1,"8.8.8.8"' # google DNS
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      # also collect multiple URC responses
      status, response = self._AT_wait_for_urc("+QPING: 0,4", self._DEFAULT_TIMEOUT)
      if status:
        self._my_logger.debug(response)
        return status, cmd, response
    return False, cmd, None

  def AT_QNTP(self):
    # request time from NTP server
    cmd = 'AT+QNTP=1,"nl.pool.ntp.org",123' # google DNS
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      # also collect multiple URC responses
      status, response = self._AT_wait_for_urc("+QNTP:", self._DEFAULT_TIMEOUT)
      if status:
        self._my_logger.debug(response)
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
      if line.startswith(urc):
        r = line.split(":")[1].strip()
        return True, r
    return False, None

  def AT_QGPSCFG_PRIO(self, gnss_prio=1):
    # set GNSS priority to 0 (GNSS) or 1 (WWAN)
    cmd = f'AT+QGPSCFG="priority",{gnss_prio},0'
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_QGPS_ON(self):
    # switch GNSS ON
    cmd = f'AT+QGPS=1,1'
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_QGPS_END(self):
    # switch GNSS OFF
    cmd = f'AT+QGPSEND'
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_QGPS_STATUS_REQUEST(self):
    # query GNSS ON/OFF status
    cmd = f'AT+QGPS?'
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, None

  def AT_QGPSLOC_REQUEST(self):
    # query GNSS location
    cmd = f'AT+QGPSLOC?'
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, response


############################################################################################################
# QUECTEL SSL FUNCTIONS
############################################################################################################

  def AT_QSSLCFG_SSLVERSION(self):
    # set SSL verification mode to 0 (SSL3.0), 1 (TLS1.0), 2 (TLS1.1), 3 (TLS1.2), 4 (all)
    cmd = f'AT+QSSLCFG="sslversion",1,4'
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, response

  def AT_QSSLCFG_CIPHERSUITE(self):
    # set SSL cipher suite to: all
    cmd = f'AT+QSSLCFG="ciphersuite",1,0xFFFF'
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, response

  #TODO: add support for CA certificates
  def AT_QSSLCFG_SECLEVEL(self):
    # set SSL security level to 0 (no CA certificate verification)
    cmd = f'AT+QSSLCFG="seclevel",1,0'
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
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

  def AT_QHTTPCFG_REQUEST(self):
    # query IP address
    cmd = f'AT+QHTTPCFG?'
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, response

  def AT_QHTTPCFG_RESPONSEHEADER(self, on=False):
    # set SSL context ID to 1
    cmd = f'AT+QHTTPCFG="responseheader",1' if on else f'AT+QHTTPCFG="responseheader",0'
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, response

  def AT_QHTTPCFG_SSLCTXID(self):
    # set SSL context ID to 1
    cmd = f'AT+QHTTPCFG="sslctxid",1'
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, response

  def AT_QIACT_REQUEST(self):
    # query IP address
    cmd = f'AT+QIACT?'
    status, response = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, response

  #TODO: fix TLS version for https://echo.free.beeceptor.com/ -> +QHTTPGET: 701
  def AT_QHTTPURL(self, url="http://postman-echo.com/get/"):
    # set URL
    URL_TIMEOUT = 80
    cmd = f'AT+QHTTPURL={len(url)}'
    status, response = self._AT_send_cmd(cmd, timeout=URL_TIMEOUT)
    if status:
      self._my_logger.debug(response)
    else:
      return False, cmd, response

    # wait for URC. ToDo analyse urc for non-0 status
    status, response2 = self._AT_send_payload(url, timeout=URL_TIMEOUT)
    response += response2
    if status:
      self._my_logger.debug(response)
      return status, cmd, response

    return False, cmd, response
  
  def AT_QHTTPGET(self):
    # send GET request
    GET_TIMEOUT = 80
    cmd = f'AT+QHTTPGET={GET_TIMEOUT}'
    status, response = self._AT_send_cmd(cmd, timeout=GET_TIMEOUT)
    if status:
      self._my_logger.debug(response)
    else:
      return False, cmd, response

    # wait for URC. ToDo analyse urc for non-0 status
    status, response = self._AT_wait_for_urc("+QHTTPGET:", GET_TIMEOUT)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response
    return False, cmd, response

  def AT_QHTTPPOST(self, body="test=1234"):
    # send POST request
    POST_TIMEOUT = 80
    cmd = f'AT+QHTTPPOST={len(body)},{POST_TIMEOUT},{POST_TIMEOUT}'
    status, response = self._AT_send_cmd(cmd, timeout=POST_TIMEOUT)
    if status:
      self._my_logger.debug(response)
    else:
      return False, cmd, response

    # send payload
    status, response2 = self._AT_send_payload(body, timeout=POST_TIMEOUT)
    response += response2
    if status:
      self._my_logger.debug(response)
    else:
      return False, cmd, response

    # wait for URC. ToDo analyse urc for non-0 status
    status, response = self._AT_wait_for_urc("+QHTTPPOST:", POST_TIMEOUT)
    if status:
      self._my_logger.debug(response)
      return status, cmd, response

    return False, cmd, response

  def AT_QHTTPREAD(self):
    # read GET response
    READ_TIMEOUT = 80
    cmd = f'AT+QHTTPREAD={READ_TIMEOUT}'
    status, response = self._AT_send_cmd(cmd, timeout=READ_TIMEOUT)
    if status:
      self._my_logger.debug(response)
    else:
      return False, cmd, response
    
    # read payload
    status, payload = self._AT_receive_payload(READ_TIMEOUT)
    if status:
      self._my_logger.debug(f"Get payload =\n{response}")
    else:
      return False, cmd, response

    # wait for URC. ToDo analyse urc for non-0 status
    status, response = self._AT_wait_for_urc("+QHTTPREAD:", self._DEFAULT_TIMEOUT)
    if status:
      self._my_logger.debug(response)
    else:
      return False, cmd, response

    return status, cmd, payload
