from bg95_serial import bg95_serial
import re
from typing import Tuple, Dict

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
  # various timeouts in [sec]
  _DEFAULT_TIMEOUT = 5
  _URL_TIMEOUT = 80
  _GET_TIMEOUT = 80
  _POST_TIMEOUT = 80
  _READ_TIMEOUT = 80

  _my_logger = None


  def __init__(self, logger=None):
    self._my_logger = logger
    super().__init__(logger=self._my_logger, default_timeout = self._DEFAULT_TIMEOUT)

############################################################################################################
# BASIC AT CMD HELPER FUNCTIONS
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
          self._my_logger.debug(f"response for {cmd} = \n{response}")
          return True, response
        elif line.startswith(self._RESPONSES_NOK): 
          self._my_logger.error(f"response for {cmd} = \n{response}")
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
          self._my_logger.debug(f"response for 'send payload' = \n{response}")
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
          self._my_logger.debug(f"response for 'receive payload' = \n{response}")
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
          self._my_logger.debug(f"response for 'wait for urc' = \n{response}")
          return True, response
      else:
        self._my_logger.error(f"incorrect response for {urc}")
        return False, response

  def _AT_cmd_wrapper(self, cmd="", timeout=_DEFAULT_TIMEOUT):
    status, response = self._AT_send_cmd(self, cmd="", timeout=self._DEFAULT_TIMEOUT)
    return status, response

  def strip_response(self, response, urc):
    return response.lstrip(urc).rstrip("\nOK\n")  
  
############################################################################################################
# QUECTEL GENERAL COMMANDS
############################################################################################################

  def AT(self):
    # Generic AT command to check if modem is alive
    cmd = "AT"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      response = {"result": "OK"}
    else:
      response = {"result": "ERROR"}
    return status, cmd, response

  def ATI(self):
    # Request product identification information
    cmd = "ATI"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex = r'(?P<man>\w+)(\r\n|\r|\n)(?P<mod>[\w\-]+)(\r\n|\r|\n)Revision: (?P<rev>\w+)(\r\n|\r|\n)OK'
      match = re.search(regex, cmd_res)
      response = {"result": "OK", 
                  "Manufacturer": match.group('man'), 
                  "Model": match.group('mod'), 
                  "Revision": match.group('rev')}
    else:
      response = {"result": "ERROR", 
                  "Manufacturer": "???", 
                  "Model": "???", 
                  "Revision": "???"}
    return status, cmd, response

  def AT_GSN(self):
    # Request product serial number identification (IMEI  number)
    cmd = "AT+GSN"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex = r'(?P<imei>\d+)'
      match = re.search(regex, cmd_res)
      response = {"result": "OK", 
                  "IMEI": match.group('imei')}
    else:
      response = {"result": "ERROR", 
                  "IMEI": "???"}
    return status, cmd, response

  def ATE(self, echo_on=True):
    # Set echo on or off
    cmd = "ATE1" if echo_on else "ATE0"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      response = {"result": "OK", 
                  "Echo": "ON" if echo_on else "OFF"}
    else:
      response = {"result": "ERROR", 
                  "Echo": "???"}
    return status, cmd, response
  
  def AT_CFUN(self, radio_on=False):
    # Set radio on or off
    cmd = "AT+CFUN=1" if radio_on else "AT+CFUN=0"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      if radio_on:
        urcs = ["+CPIN: READY", "+QUSIM: 1", "+QIND: SMS DONE"]
        for urc in urcs:
          if not self._AT_wait_for_urc(urc, timeout=10):
            status = False
            response = {"result": "ERROR", 
                        "RADIO": "OFF"}
          else:
            response = {"result": "OK", 
                        "RADIO": "ON"}
      else:
        response = {"result": "ERROR", 
                    "RADIO": "OFF"}
    else:
      response = {"result": "ERROR", 
                  "RADIO": "OFF"}
    return status, cmd, response

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
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex = r'(?P<imsi>\d+)'
      match = re.search(regex, cmd_res)
      response = {"result": "OK", 
                  "IMSI": match.group('imsi')}
    else:
      response = {"result": "ERROR", 
                  "IMSI": "???"}
    return status, cmd, response

  def AT_QCCID_REQUEST(self):
    # Request SIMs CCID number, note: only valid after CFUN=1
    cmd = "AT+QCCID"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex = r'\+QCCID: (?P<ccid>\w+)'
      match = re.search(regex, cmd_res)
      response = {"result": "OK", 
                  "CCID": match.group('ccid')}
    else:
      response = {"result": "ERROR", 
                  "CCID": "???"}
    return status, cmd, response

############################################################################################################
# QUECTEL NETWORK SERVICE COMMANDS
############################################################################################################

  def AT_CREG(self):
    # Request GSM network registration status
    GSM_REGISTRATION_STAT_UNKNOWN = 4
    cmd = "AT+CREG?"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex = r'\+CEREG: (?P<cid>\d+),(?P<gsm_registration_stat>\d+)'
      match = re.search(regex, cmd_res)
      gsm_registration_stat = int(match.group('gsm_registration_stat'))
      # 0=not registered, 1=registered, 2=not registered, searching, 3=registration denied, 4=unknown, 5=registered, roaming
      if gsm_registration_stat in [1,5]:
        response = {"result": "OK", 
                    "gsm_registration_stat": gsm_registration_stat}
      else:
        response = {"result": "ERROR", 
                    "gsm_registration_stat": gsm_registration_stat}
    else:
      response = {"result": "ERROR", 
                  "gsmregistration_stat": GSM_REGISTRATION_STAT_UNKNOWN}
    return status, cmd, response

  def AT_COPS_REQUEST(self):
    # Request current operator
    cmd = "AT+COPS?"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex = r'\+COPS: (?P<mode>\d+),(?P<format>\d+),"(?P<operator>([\w\s]+))",(?P<act>\d+)'
      match = re.search(regex, cmd_res)
      response = {"result": "OK", 
                  "mode": int(match.group('mode')), 
                  "format": int(match.group('format')), 
                  "operator": match.group('operator'),
                  "act": int(match.group('act'))}
    else:
      response = {"result": "ERROR", 
                  "mode": 0, 
                  "format": 0, 
                  "operator": "???", 
                  "act": 0}
    return status, cmd, response

  def AT_CSQ(self):
    # Request signal quality (RSSI)
    cmd = "AT+CSQ"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex = r'\+CSQ: (?P<rssi>\d+),(?P<ber>\d+)'
      match = re.search(regex, cmd_res)
      response = {"result": "OK", "rssi": 
                  int(match.group('rssi'))}
    else:
      response = {"result": "ERROR", 
                  "rssi": 99}
    return status, cmd, response

  def AT_QNWINFO(self):
    # Request network information
    cmd = "AT+QNWINFO"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex = r'\+QNWINFO: "(?P<act>\w+)","(?P<operator>\w+)","(?P<band>([\w\s]+))",(?P<channel>\d+)'
      match = re.search(regex, cmd_res)
      response = {"result": "OK", 
                  "act": match.group('act'), 
                  "operator": match.group('operator'), 
                  "band" : match.group('band'), 
                  "channel": int(match.group('channel')) }
    else:
      response = {"result": "ERROR", 
                  "act": "???", 
                  "operator": "???", 
                  "band": "???", 
                  "channel": 0}
    return status, cmd, response

  def AT_QCSQ(self):
    # Request network information
    cmd = "AT+QCSQ"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex = r'\+QCSQ: "(?P<sysmode>\w+)",'
      match = re.search(regex, cmd_res)
      sysmode = match.group('sysmode')
      if sysmode in ["NOSERVICE"]:
        response = {"result": "ERROR", "sysmode": sysmode}
      elif sysmode in ["GSM"]:
        regex = r'\+QCSQ: "(?P<sysmode>\w+)",(?P<rssi>[\d\-]+),'
        match = re.search(regex, cmd_res)
        response = {"result": "OK", "sysmode": sysmode, 
                    "gsm_rssi": int(match.group('rssi'))}
      elif sysmode in ["eMTC", "NBIoT"]:
        regex = r'\+QCSQ: "(?P<sysmode>\w+)",(?P<rssi>[\d\-]+),(?P<rsrp>[\d\-]+),(?P<sinr>[\d\-]+),(?P<rsrq>[\d\-]+)'
        match = re.search(regex, cmd_res)
        response = {"result": "OK", 
                    "sysmode": sysmode, 
                    "lte_rssi": int(match.group('rssi')), 
                    "lte_rsrp": int(match.group('rsrp')), 
                    "lte_sinr": int(match.group('sinr')), 
                    "lte_rsrq": int(match.group('rsrq'))}
    else:
      response = {"result": "ERROR", 
                  "sysmode": "???", 
                  "lte_rssi": 0, 
                  "lte_rsrp": 0, 
                  "lte_sinr": 0, 
                  "lte_rsrq": 0}
    return status, cmd, response
  
############################################################################################################
# QUECTEL SMS COMMANDS
############################################################################################################

############################################################################################################
# QUECTEL PACKET DOMAIN COMMANDS
############################################################################################################

  def AT_CGATT_REQUEST(self):
    # Request Packet Domain Service (PS) attach status
    PS_DETACHED = 0
    cmd = "AT+CGATT?"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex = r'\+CGATT: (?P<ps_attach>\d+)'
      match = re.search(regex, cmd_res)
      response = {"result": "OK", 
                  "PS_attach": int(match.group('ps_attach'))}
    else:
      response = {"result": "ERROR", 
                  "PS_attach": PS_DETACHED} 
    return status, cmd, response
  
  def AT_CGDCONT_REQUEST(self):
    # Request PDP context
    cmd = "AT+CGDCONT?"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex = r'\+CGDCONT: (?P<cid>\d+),"(?P<pdp_type>\w+)","(?P<apn>[\w\.]+)","(?P<pdp_addr>[\w\.]+)"'
      match = re.search(regex, cmd_res)
      response = {"result": "OK", 
                  "CID": int(match.group('cid')), 
                  "PDP_type": match.group('pdp_type'), 
                  "APN": match.group('apn'), 
                  "PDP_addr": match.group('pdp_addr')}
    else:
      response = {"result": "ERROR", 
                  "CID": 0, 
                  "PDP_type": "???", 
                  "APN": "???", 
                  "PDP_addr": "0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0"} 
    return status, cmd, response
  
  def AT_CGACT_REQUEST(self):
    # Request PDP context
    cmd = "AT+CGACT?"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex = r'\+CGACT: (?P<cid>\d+),(?P<state>\d+)'
      match = re.search(regex, cmd_res)
      response = {"result": "OK", 
                  "CID": int(match.group('cid')), 
                  "state": int(match.group('state'))}
    else:
      response = {"result": "ERROR", 
                  "CID": 0, 
                  "state": 0} 
    return status, cmd, response

  def AT_CGPADDR_REQUEST(self):
    # Request PDP IP address
    cmd = "AT+CGPADDR=" + str(self._CID)
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex = r'\+CGPADDR: (?P<cid>\d+),(?P<ip_address>[\w\.]+)'
      match = re.search(regex, cmd_res)
      response = {"result": "OK", "CID": int(match.group('cid')), "IP_address": match.group('ip_address')}
    else:
      response = {"result": "ERROR", "CID": 0, "IP_address": "0.0.0.0"} 
    return status, cmd, response

  def AT_CGREG_REQUEST(self):
    # Request EGPRS network registration status
    # NOTE: only call when CFUN=1, otherwise an error will be returned
    EGPRS_REGISTRATION_STAT_UNKNOWN = 4
    cmd = "AT+CGREG?"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex = r'\+CGREG: (?P<cid>\d+),(?P<egprs>\d+)'
      match = re.search(regex, cmd_res)
      egprs_registration_stat = int(match.group('egprs'))
      # 0=not registered, 1=registered, 2=not registered, searching, 3=registration denied, 4=unknown, 5=registered, roaming
      if egprs_registration_stat in [1,5]:
        response = {"result": "OK", "egprs_registration_stat": egprs_registration_stat}
      else:
        response = {"result": "ERROR", "egprs_registration_stat": egprs_registration_stat}
    else:
      response = {"result": "ERROR", "n": 0, "egprs_registration_stat": EGPRS_REGISTRATION_STAT_UNKNOWN} 
    return status, cmd, response
  
  def AT_CEREG(self):
    # Request LTE network registration status
    EPS_REGISTRATION_STAT_UNKNOWN = 4
    cmd = "AT+CEREG?"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex = r'\+CEREG: (?P<cid>\d+),(?P<eps>\d+)'
      match = re.search(regex, cmd_res)
      eps_registration_stat = int(match.group('eps'))
      # 0=not registered, 1=registered, 2=not registered, searching, 3=registration denied, 4=unknown, 5=registered, roaming
      if eps_registration_stat in [1,5]:
        response = {"result": "OK", "eps_registration_stat": eps_registration_stat}
      else:
        response = {"result": "ERROR", "eps_registration_stat": eps_registration_stat}
    else:
      response = {"result": "ERROR", "n": 0, "eps_registration_stat": EPS_REGISTRATION_STAT_UNKNOWN} 
    return status, cmd, response
  
############################################################################################################
# QUECTEL HARDWARE RELATED FUNCTIONS
############################################################################################################

  def AT_POWERDOWN(self):
    # Modem power down, 0=immediate, 1=normal mode
    cmd = "AT+POWD=1"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      response = {"result": "OK"}
      #ToDo: wait for "POWERED DOWN" URC
    else:
      response = {"result": "ERROR"}
 
    return status, cmd, response
  
  def AT_CCLK_REQUEST(self):
    # Request PDP context
    cmd = "AT+CCLK?"
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex_pattern = r'\+CCLK: \"(?P<date>[0-9/]*),(?P<time>[0-9:+]*)\"'
      match = re.search(regex_pattern, cmd_res)
      response = {"result": "OK", 
                  "date": match.group('date'), 
                  "time": match.group('time')}
    else:
      response = {"result": "ERROR", "date": "00/00/00", "time": "00:00:00+0"} 
    return status, cmd, response
  
  def AT_QTEMP(self):
    # request silicon temperatures
    cmd = 'AT+QTEMP'
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex_pattern = r'\+QTEMP: (?P<pmic>\d+),(?P<xo>\d+),(?P<pa>\d+),(?P<misc>\d+)'
      match = re.search(regex_pattern, cmd_res)
      response = {"result": "OK", 
                  "T_pmic": int(match.group('pmic')), 
                  "T_xo": int(match.group('xo')), 
                  "T_pa": int(match.group('pa')), 
                  "T_misc": int(match.group('misc'))}
    else:
      response = {"result": "ERROR", "T_pmic": 0, "T_xo": 0, "T_pa": 0, "T_misc": 0} 
    return status, cmd, response

############################################################################################################
# QUECTEL TCPIP FUNCTIONS
############################################################################################################

  IP_ERROR_CODES =  {
    0:   "operate successfully",
    550: "unknown error",
    551: "operation blocked",
    552: "invalid parameters",
    553: "Memory allocation failed",
    554: "create socket failed",
    555: "operation not supported",
    556: "socket bind failed",
    557: "socket listen failed",
    558: "socket write failed",
    559: "socket read failed",
    560: "socket accept failed",
    561: "Activate pdp context failed",
    562: "Deactivate pdp context failed",
    563: "socket identity has been used",
    564: "dns busy"
  }

  PDP_CONTEXT_ID = 1

  def AT_QIACT(self) -> Tuple[bool, str, Dict[str, str]]:
    # Activate a specified PDP context
    cmd = f'AT+QIACT={self.PDP_CONTEXT_ID}'
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      response = {"result": "OK"}
    else:
      response = {"result": "ERROR"}
    return status, cmd, response

  def AT_QIDEACT(self) -> Tuple[bool, str, Dict[str, str]]:
    # Deactivate a specified PDP context
    cmd = f'AT+QIDEACT={self.PDP_CONTEXT_ID}'
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      response = {"result": "OK"}
    else:
      response = {"result": "ERROR"}
    return status, cmd, response

  def AT_QIACT_REQUEST(self) -> Tuple[bool, str, Dict[str, str | int]]:
    # query context type and state and IP address. Requires that PDP context is activated first
    cmd = f'AT+QIACT?'
    status, cmd_res = self._AT_send_cmd(cmd)
    # default response
    response = {"result": "ERROR", 
                "pdp_context_id": 0, 
                "context_state": 0, 
                "context_type": 0, 
                "ip_address": "0:0:0:0"}
    if status:
      if "+QIACT: " in cmd_res:
        regex_pattern = r'\+QIACT: (?P<pdp_context_id>\d+),(?P<context_state>\d+),(?P<context_type>\d+),"(?P<ip_address>[\w.]+)"'
        match = re.search(regex_pattern, cmd_res)
        response = {"result": "OK", 
                    "pdp_context_id": int(match.group('pdp_context_id')), 
                    "context_state": int(match.group('context_state')), 
                    "context_type": int(match.group('context_type')), 
                    "ip_address": match.group('ip_address')}
      else:
        response = {"result": "NO_PDP_CONTEXT"}
    else:
      response = {"result": "ERROR"}
    return status, cmd, response

  def AT_QICSGP_REQUEST(self) -> Tuple[bool, str, Dict[str, str]]:
    cmd = "AT+QICSGP=1"
    status, response = self._AT_send_cmd(cmd)
    if status:
      response = {"result": "OK"}
    else:
      response = {"result": "ERROR"}
    return status, cmd, response

  def AT_QPING(self) -> Tuple[bool, str, Dict[str, str | int]]:
    # ping an IP address
    # cmd = 'AT+QPING=1,"45.82.191.174"' # www.felixdonkers.nl
    cmd = 'AT+QPING=1,"8.8.8.8"' # google DNS
    status, response = self._AT_send_cmd(cmd)
    # default response
    response = {"result": "ERROR",
                "finresult": 550,
                "sent": 0,
                "rcvd": 0,
                "lost": 0,
                "min": 0,
                "max": 0,
                "avg": 0}
    if status:
      self._my_logger.debug(response)
      # also collect multiple URC responses
      status, urc_res = self._AT_wait_for_urc("+QPING: 0,4", self._DEFAULT_TIMEOUT)
      if status:
        regex_pattern = r'\+QPING: (?P<finresult>\d+),(?P<sent>\d+),(?P<rcvd>\d+),(?P<lost>\d+),(?P<min>\d+),(?P<max>\d+),(?P<avg>\d+)'
        match = re.search(regex_pattern, urc_res)
        response = {"result": "OK",
                    "finresult": int(match.group('finresult')),
                    "sent": int(match.group('sent')),
                    "rcvd": int(match.group('rcvd')),
                    "lost": int(match.group('lost')),
                    "min": int(match.group('min')),
                    "max": int(match.group('max')),
                    "avg": int(match.group('avg'))}
      else:
        response = {"result": "ERROR"}
    else:
      response = {"result": "ERROR"}
    return status, cmd, response

  def AT_QNTP(self) -> Tuple[bool, str, Dict[str, str | int]]:
    # request time from NTP server
    cmd = 'AT+QNTP=1,"nl.pool.ntp.org",123' # google DNS
    status, cmd_res = self._AT_send_cmd(cmd)
    # default response
    response = {"result": "ERROR",
                "finresult": 550,
                "date": "00/00/00",
                "time": "00:00:00+00"}
    if status:
      self._my_logger.debug(response)
      # also collect multiple URC responses
      status, urc_res = self._AT_wait_for_urc("+QNTP: ", self._DEFAULT_TIMEOUT)
      if status:
        regex_pattern = r'\+QNTP: (?P<finresult>\d+),"(?P<date>[\w\/]+),(?P<time>[\w\:\-\+]+)"'
        match = re.search(regex_pattern, urc_res)

        response = {"result": "OK",
                    "finresult": int(match.group('finresult')),
                    "date": match.group('date'),
                    "time": match.group('time')}
        self._my_logger.debug(response)
      else:
        response = {"result": "ERROR"}
    else:
      response = {"result": "ERROR"}
    return status, cmd, response


############################################################################################################
# QUECTEL GNSS FUNCTIONS
############################################################################################################

  #TODO: new format for responses

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

  def AT_QGPSCFG_PRIO(self, gnss_prio=1) -> Tuple[bool, str, Dict[str, str | int]]:
    # set GNSS priority to 0 (GNSS) or 1 (WWAN)
    cmd = f'AT+QGPSCFG="priority",{gnss_prio},0'
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      response = {"result": "OK"}
    else:
      response = {"result": "ERROR"}
    return status, cmd, response

  def AT_QGPS_ON(self) -> Tuple[bool, str, Dict[str, str | int]]:
    # switch GNSS ON
    cmd = f'AT+QGPS=1,1'
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      response = {"result": "OK", 
                  "gps_on": True}
    else:
      response = {"result": "ERROR", 
                  "gps_on": False}
    # self._my_logger.debug(response)
    return status, cmd, response

  def AT_QGPS_END(self) -> Tuple[bool, str, Dict[str, str | int]]:
    # switch GNSS OFF
    cmd = f'AT+QGPSEND'
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      response = {"result": "OK", 
                  "gps_on": False}
    else:
      response = {"result": "ERROR", 
                  "gps_on": True}
    # self._my_logger.debug(response)
    return status, cmd, response

  def AT_QGPS_STATUS_REQUEST(self) -> Tuple[bool, str, Dict[str, str | int]]:
    # query GNSS ON/OFF status
    cmd = f'AT+QGPS?'
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex_pattern = r'\+QGPS: (?P<status>\d+)'
      match = re.search(regex_pattern, cmd_res)
      response = {"result": "OK",
                  "gps_on": True if (int(match.group('status')) == 1) else False}
      self._my_logger.debug(response)
    else:
      response = {"result": "ERROR",
                  "gps_on": False}
    return status, cmd, response

  def AT_QGPSLOC_REQUEST(self) -> Tuple[bool, str, Dict[str, str | int]]:
    # query GNSS location
    default_response = {"result": "ERROR",
                        "gps_error": 549, # unknown error
                        "utc_time": "0.0",
                        "latitude": "0.0N",
                        "longitude": "0.0E"}
    cmd = f'AT+QGPSLOC?'
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      self._my_logger.debug(cmd_res)
      if ("+QGPSLOC: " in cmd_res):
        regex_pattern = r'\+QGPSLOC: (?P<utc_time>[\d\.]+),(?P<latitude>[\w\.]+),(?P<longitude>[\w\.]+),'
        match = re.search(regex_pattern, cmd_res)
        response = {"result": "OK",
                    "gps_error": 0, # no error, we have a fix 
                    "utc_time": match.group('utc_time'),
                    "latitude": match.group('latitude'),
                    "longitude": match.group('longitude')}
      elif ("+CME ERROR: 516" in cmd_res):
        response = default_response
        response["gps_error"] = 516 # no fix
      else:
        response = default_response
    else:
      response = default_response
    return status, cmd, response


############################################################################################################
# QUECTEL SSL FUNCTIONS
############################################################################################################

  def AT_QSSLCFG_SSLVERSION(self) -> Tuple[bool, str, Dict[str, str | int]]:
    # set SSL verification mode to 0 (SSL3.0), 1 (TLS1.0), 2 (TLS1.1), 3 (TLS1.2), 4 (all)
    cmd = f'AT+QSSLCFG="sslversion",1,4'
    status, response = self._AT_send_cmd(cmd)
    if status:
      response = {"result": "OK"}
    else:
      response = {"result": "ERROR"}
    return status, cmd, response

  def AT_QSSLCFG_CIPHERSUITE(self) -> Tuple[bool, str, Dict[str, str | int]]:
    # set SSL cipher suite to: all
    cmd = f'AT+QSSLCFG="ciphersuite",1,0xFFFF'
    status, response = self._AT_send_cmd(cmd)
    if status:
      response = {"result": "OK"}
    else:
      response = {"result": "ERROR"}
    return status, cmd, response

  #TODO: add support for CA certificates
  def AT_QSSLCFG_SECLEVEL(self) -> Tuple[bool, str, Dict[str, str | int]]:
    # set SSL security level to 0 (no CA certificate verification)
    cmd = f'AT+QSSLCFG="seclevel",1,0'
    status, response = self._AT_send_cmd(cmd)
    if status:
      response = {"result": "OK"}
    else:
      response = {"result": "ERROR"}
    return status, cmd, response

############################################################################################################
# QUECTEL HTTP(S) FUNCTIONS
############################################################################################################

  HTTPS_ERROR = {
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

  def AT_QHTTPCFG_REQUEST(self) -> Tuple[bool, str, Dict[str, str | int]]:
    # query IP address
    cmd = f'AT+QHTTPCFG?'
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      regex = r'[.\s]*"contextid",(?P<contextid>\d+)'
      match = re.search(regex, cmd_res)
      contextid = int(match.group('contextid'))

      regex = r'[.\s]*"requestheader",(?P<requestheader>\d+)'
      match = re.search(regex, cmd_res)
      requestheader = int(match.group('requestheader'))

      regex = r'[.\s]*"responseheader",(?P<responseheader>\d+)'
      match = re.search(regex, cmd_res)
      responseheader = int(match.group('responseheader'))

      regex = r'[.\s]*"sslctxid",(?P<sslctxid>\d+)'
      match = re.search(regex, cmd_res)
      sslctxid = int(match.group('sslctxid'))

      regex = r'[.\s]*"contenttype",(?P<contenttype>\d+)'
      match = re.search(regex, cmd_res)
      contenttype = int(match.group('contenttype'))

      regex = r'[.\s]*"auth","(?P<auth>[\w\:]*)"'
      match = re.search(regex, cmd_res)
      auth = match.group('auth')

      regex = r'[.\s]*"custom_header","(?P<custom_header>[\w]*)"'
      match = re.search(regex, cmd_res)
      custom_header = match.group('custom_header')

      response = {"result": "OK",
                  "contextid": contextid,
                  "requestheader": requestheader,
                  "responseheader": responseheader,
                  "sslctxid": sslctxid,
                  "contenttype": contenttype,
                  "auth": auth,
                  "custom_header": custom_header}  
    else:
      response = {"result": "ERROR"}  
    return status, cmd, response

  def AT_QHTTPCFG_RESPONSEHEADER(self, on=False) -> Tuple[bool, str, Dict[str, str | int]]:
    # set SSL context ID to 1
    cmd = f'AT+QHTTPCFG="responseheader",1' if on else f'AT+QHTTPCFG="responseheader",0'
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      response = {"result": "OK"}
    else:
      response = {"result": "ERROR"}
    return status, cmd, response

  def AT_QHTTPCFG_SSLCTXID(self) -> Tuple[bool, str, Dict[str, str | int]]:
    # set SSL context ID to 1
    cmd = f'AT+QHTTPCFG="sslctxid",1'
    status, cmd_res = self._AT_send_cmd(cmd)
    if status:
      response = {"result": "OK"}
    else:
      response = {"result": "ERROR"}
    return status, cmd, response

  def AT_QHTTPURL(self, url="http://postman-echo.com/get/") -> Tuple[bool, str, Dict[str, str | int]]:
    # set URL for HTTP GET/POST
    #TODO: fix TLS version for https://echo.free.beeceptor.com/ -> +QHTTPGET: 701
    default_response = {"result": "ERROR"}
    cmd = f'AT+QHTTPURL={len(url)}'
    status, cmd_res = self._AT_send_cmd(cmd, timeout=self._URL_TIMEOUT)
    if (status != True) or ("CONNECT" not in cmd_res):
      return False, cmd, default_response

    # send URL
    status, cmd_res = self._AT_send_payload(url, timeout=self._URL_TIMEOUT)
    if status:
      response = {"result": "OK"}
    else:
      response = {"result": "ERROR"}
    return status, cmd, response
  
  def AT_QHTTPGET(self) -> Tuple[bool, str, Dict[str, str | int]]:
    # send GET request
    default_response = {"result": "ERROR", 
                        "httprspcode": 0, 
                        "datalen": 0}
    cmd = f'AT+QHTTPGET={self._GET_TIMEOUT}'
    status, cmd_res = self._AT_send_cmd(cmd, timeout=self._GET_TIMEOUT)
    if status != True:
      return False, cmd, default_response

    # wait for URC
    status, urc_res = self._AT_wait_for_urc("+QHTTPGET:", self._GET_TIMEOUT)
    regex = r'\+QHTTPGET: (?P<result>\d+),(?P<httprspcode>\d+),(?P<datalen>\d+)'
    match = re.search(regex, urc_res)

    if status:
      if (int(match.group('result')) == 0) and (int(match.group('httprspcode')) == 200):
        response = default_response
        response["result"] = "OK"
        response["httprspcode"] = int(match.group('httprspcode'))
        response["datalen"] =int(match.group('datalen'))
      else:
        response = default_response
    else: 
      response = default_response

    return status, cmd, response

  def AT_QHTTPPOST(self, body="test=1234") -> Tuple[bool, str, Dict[str, str | int]]:
    # send POST request
    default_response = {"result": "ERROR", 
                        "httprspcode": 0, 
                        "datalen": 0}
    cmd = f'AT+QHTTPPOST={len(body)},{self._POST_TIMEOUT},{self._POST_TIMEOUT}'
    status, cmd_res = self._AT_send_cmd(cmd, timeout=self._POST_TIMEOUT)
    if status != True:
      return False, cmd, default_response

    # send payload
    status, cmd_res = self._AT_send_payload(body, timeout=self._POST_TIMEOUT)
    if status != True:
      return False, cmd, default_response

    # wait for URC. ToDo analyse urc for non-0 status
    status, urc_res = self._AT_wait_for_urc("+QHTTPPOST:", self._POST_TIMEOUT)
    regex = r'\+QHTTPPOST: (?P<result>\d+),(?P<httprspcode>\d+),(?P<datalen>\d+)'
    match = re.search(regex, urc_res)

    if status:
      if (int(match.group('result')) == 0) and (int(match.group('httprspcode')) == 200):
        response = default_response
        response["result"] = "OK"
        response["httprspcode"] = int(match.group('httprspcode'))
        response["datalen"] =int(match.group('datalen'))
      else:
        response = default_response
    else: 
      response = default_response

    return status, cmd, response

  def AT_QHTTPREAD(self) -> Tuple[bool, str, Dict[str, str | int]]:
    # read GET response
    default_response = {"result": "ERROR", 
                        "payload": ""}
    cmd = f'AT+QHTTPREAD={self._READ_TIMEOUT}'
    status, response = self._AT_send_cmd(cmd, timeout=self._READ_TIMEOUT)
    if status != True:
      return False, cmd, default_response
    
    # read payload
    status, payload = self._AT_receive_payload(self._READ_TIMEOUT)
    if status != True:
      return False, cmd, default_response

    # wait for URC. ToDo analyse urc for non-0 status
    status, urc_res = self._AT_wait_for_urc("+QHTTPREAD:", self._DEFAULT_TIMEOUT)
    if status != True:
      return False, cmd, default_response

    response = {"result": "OK", 
                "payload": payload}
    return status, cmd, response
