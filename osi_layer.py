import logging
import time
from timer import timer
from bg95_atcmds import bg95_atcmds

class osi_layer(bg95_atcmds):
  _AT_CMD_RETRY_INTERVAL = .25

  def __init__(self, logger=None):
    self._my_logger = logger
    super().__init__(logger=self._my_logger)

############################################################################################################
# PHYSICAL LINK LAYER FUNCTIONS
############################################################################################################

  def run_modem_GNSS_commands(self):
    #ToDo: add 'assisted GNSS' commands, e.g. XTRA file download, etc

    # set priority to GNSS
    status, cmd, response = self.AT_QGPSCFG_PRIO(gnss_prio=0)
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False, None

    # check if GNSS is already ON
    status, cmd, response = self.AT_QGPS_STATUS_REQUEST()
    if status:
      logging.debug(f"GPS is ON") if (response['gps_on'] == True) else logging.debug(f"GPS is OFF")
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False, None

    # switch ON GNSS if not already ON  
    if not response["gps_on"]:
      status, cmd, response = self.AT_QGPS_ON()
      if status:
        logging.debug(f"{cmd} PASSED! with response:\n{response}")
        logging.debug(f"GPS is turned ON") if (response['gps_on'] == True) else logging.error(f"GPS is still OFF")
      else:
        logging.error(f"{cmd} FAILED!")
        return False, None

    # check if GNSS is indeed switched ON
    status, cmd, response = self.AT_QGPS_STATUS_REQUEST()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response['gps_on']}")
      logging.debug(f"GPS is ON") if (response['gps_on'] == True) else logging.error(f"GPS is still OFF")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    # get GPS location
    status = False
    while not status:
      time.sleep(1)
      status, cmd, response = self.AT_QGPSLOC_REQUEST()
      if not status and (response["gps_error"] == 516):
        logging.error("GNSS GOT NO FIX!")

    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
      logging.debug(f"Timestamp = {response['utc_time']}")
      logging.debug(f"Latitude  = {response['latitude']}")
      logging.debug(f"Longitude = {response['longitude']}\n")
    else:
      logging.error(f"{cmd} FAILED!")
      logging.error(f"returned {response}")
      return False, None

    # switch OFF GNSS
    status, cmd, response = self.AT_QGPS_END()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response['result']}")
      logging.debug(f"GPS is NOT switched OFF") if (response['gps_on'] == True) else logging.debug(f"GPS is switched OFF")
    else:
      logging.error(f"{cmd} FAILED!")
      return False, None

    # set priority back to WWAN
    status, cmd, response = self.AT_QGPSCFG_PRIO(gnss_prio=1)
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False, None

    return True, response
  
############################################################################################################
# DATA LINK LAYER FUNCTIONS
############################################################################################################

  def run_modem_general_at_commands(self):
    status = self.AT()
    # check if modem is alive
    if status:
      logging.debug(f"PASSED!")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    status, cmd, response = self.ATI()
    # request product information
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    status, cmd, response = self.ATE(True)
    # turn on echo
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    status, cmd, response = self.AT_GSN()
    # request IMEI
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    status, cmd, response = self.AT_CCLK_REQUEST()
    # request current time
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    status, cmd, response = self.AT_QTEMP()
    # request silicon temperatures
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    return True

############################################################################################################
# NETWORK LAYER FUNCTIONS
############################################################################################################

  def connect_modem_to_network(self):
    # make sure to be disconnected first
    status, cmd, response = self.AT_CFUN(0)
    if status:
      logging.debug(f"{cmd} PASSED!")

    # connect to network
    status, cmd, response = self.AT_CFUN(1)
    if status:
      logging.debug(f"{cmd} PASSED!")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    # wait for EPS network registration
    registered = False
    while not registered:
      status, cmd, response = self.AT_CEREG()
      if status:
        registered = (response["eps_registration_stat"] in [1,5])
      time.sleep(self._AT_CMD_RETRY_INTERVAL)
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    # wait for proper signal strength
    NO_SIGNAL = 99
    rssi = NO_SIGNAL
    while rssi == NO_SIGNAL:
      status, cmd, response = self.AT_CSQ()
      rssi = response["rssi"]
      logging.debug(f"rssi = {rssi}")
      time.sleep(self._AT_CMD_RETRY_INTERVAL)    
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    return True

  def disconnect_modem_from_network(self):
    status, cmd, response = self.AT_CFUN(0)
    if status:
      logging.debug(f"{cmd} PASSED!")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    return True

  def request_network_info(self):
    status, cmd, response = self.AT_CGATT_REQUEST()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    status, cmd, response = self.AT_QCSQ()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    status, cmd, response = self.AT_CIMI_REQUEST()
    # request IMSI, only valid after CFUN=1
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    status, cmd, response = self.AT_QCCID_REQUEST()
    # request CCID
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    status, cmd, response = self.AT_CGDCONT_REQUEST()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False
    
    status, cmd, response = self.AT_CGACT_REQUEST()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False
    
    status, cmd, response = self.AT_CGPADDR_REQUEST()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    status, cmd, response = self.AT_CGREG_REQUEST()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False
    
    status, cmd, response = self.AT_COPS_REQUEST()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    status, cmd, response = self.AT_QNWINFO()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    return True

  def run_modem_IP_commands(self):
    status, cmd, response = self.AT_QPING()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    status, cmd, response = self.AT_QNTP()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    status, cmd, response = self.AT_QICSGP_REQUEST()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    return True

############################################################################################################
# PRESENTATION LAYER FUNCTIONS
############################################################################################################

  def TLS_SETUP(self):
    status, cmd, response = self.AT_QHTTPCFG_RESPONSEHEADER(True)
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False, None

    status, cmd, response = self.AT_QHTTPCFG_SSLCTXID()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False, None

    status, cmd, response = self.AT_QSSLCFG_SSLVERSION()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False, None

    status, cmd, response = self.AT_QSSLCFG_CIPHERSUITE()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False, None

    status, cmd, response = self.AT_QSSLCFG_SECLEVEL()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False, None

    return status, response

############################################################################################################
# APPLICATION LAYER FUNCTIONS
############################################################################################################

  def run_modem_HTTP_commands(self):
    status, cmd, response = self.AT_QHTTPCFG_REQUEST()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    status, cmd, response = self.AT_QIACT_REQUEST()
    if status and (response["result"] == "OK"):
      logging.debug(f"{cmd} PASSED! with response:\n{response['result']}")
    elif response["result"] == "NO_PDP_CONTEXT":
      logging.debug(f"{cmd} PASSED! with response:\n{response['result']}")
      status, cmd, response = self.AT_QIACT()
      if status:
        logging.debug(f"{cmd} PASSED! with response:\n{response}")
      else:
        logging.error(f"{cmd} FAILED!")
        return False
    else:
      logging.error(f"{cmd} FAILED!")
      return False

    status, cmd, response = self.AT_QIACT_REQUEST()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False
    
    return True

  def HTTP_GET(self, url):
    status, cmd, response = self.AT_QHTTPURL(url)
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False, None

    status, cmd, response = self.AT_QHTTPGET()
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False, None

    status, cmd, response = self.AT_QHTTPREAD()
    if status:
      logging.debug(f"{cmd} PASSED!")
    else:
      logging.error(f"{cmd} FAILED!")
      return False, None

    logging.debug(f"HTTP_GET PASSED! with response:\n{response["result"]}\n===payload start===\n{response["payload"]}\n===payload end===")
    return True, response

  def HTTP_POST(self, url, body):
    status, cmd, response = self.AT_QHTTPURL(url)
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False, None

    status, cmd, response = self.AT_QHTTPPOST(body)
    if status:
      logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False, None

    status, cmd, response = self.AT_QHTTPREAD()
    if status:
      logging.debug(f"{cmd} PASSED!")
    else:
      logging.error(f"{cmd} FAILED!")
      return False, None

    logging.debug(f"HTTP_POST PASSED! with response:\n{response["result"]}\n===payload start===\n{response["payload"]}\n===payload end===")
    return True, response

  def HTTPS_GET(self, url):
    status, response = self.TLS_SETUP()
    if status:
      logging.debug(f"TLS_SETUP PASSED! with response:\n{response}")
    else:
      logging.error(f"TLS_SETUP FAILED!")
      return False, None

    status, response = self.HTTP_GET(url)
    if status:
      logging.debug(f"HTTP_GET PASSED! with response:\n{response}")
    else:
      logging.error(f"HTTP_GET FAILED!")
      return False, None

    logging.debug(f"HTTPS_GET PASSED! with response:\n{response["result"]}\n===payload start===\n{response["payload"]}\n===payload end===")
    return status, response

  def HTTPS_POST(self, url, body):
    status, response = self.TLS_SETUP()
    if status:
      logging.debug(f"TLS_SETUP PASSED! with response:\n{response}")
    else:
      logging.error(f"TLS_SETUP FAILED!")
      return False, None

    # run_modem_HTTP_commands()

    status, response = self.HTTP_POST(url, body)
    if status:
      logging.debug(f"HTTP_POST PASSED! with response:\n{response}")
    else:
      logging.error(f"HTTP_POST FAILED!")
      return False, None

    logging.debug(f"HTTPS_POST PASSED! with response:\n{response["result"]}\n===payload start===\n{response["payload"]}\n===payload end===")
    return status, response

if __name__ == "__main__":
  # https://realpython.com/python-logging/ ; levels are DEBUG, INFO, WARNING, ERROR, CRITICAL
  logging.basicConfig(format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

  my_bg95 = osi_layer(logging)

  my_timer = timer(logging)

  logging.debug("\n******************************")

  # TODO: add more tests here

  logging.debug("\n******************************")
