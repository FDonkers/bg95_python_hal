import logging
import time
from timer import timer
from bg95_atcmds import bg95_atcmds

class osi_layer(bg95_atcmds):

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
        return False

    # check if GNSS is already ON
    status, cmd, response = self.AT_QGPS_STATUS_REQUEST()
    if status:
        logging.debug(f"{cmd} PASSED! with response:\n{response}")
        status, urc = self.extract_urc(response, "+QGPS")
        gps_on = (urc[0] == '1')
        logging.debug(f"GPS is ON") if (gps_on == True) else logging.info(f"GPS is OFF")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    # switch ON GNSS if not already ON  
    if not gps_on:
        status, cmd, response = self.AT_QGPS_ON()
        if status:
            logging.debug(f"{cmd} PASSED! with response:\n{response}")
        else:
            logging.error(f"{cmd} FAILED!")

    # check if GNSS is indeed switched ON
    status, cmd, response = self.AT_QGPS_STATUS_REQUEST()
    if status:
        logging.debug(f"{cmd} PASSED! with response:\n{response}")
        status, urc = self.extract_urc(response, "+QGPS")
        gps_on = (urc[0] == '1')
        logging.debug(f"GPS is ON") if (gps_on == True) else logging.info(f"GPS is OFF")
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
        status, cmd, response = self.AT_QGPSLOC_REQUEST()
        if status:
            # check if fix is obtained
            s, urc = self.extract_urc(response, "+CME ERROR")
            got_fix = (urc == None)

    if status:
        logging.debug(f"{cmd} PASSED! with response:\n{response}")
        status, res = self.extract_urc(response, "+QGPSLOC")
        logging.debug(f"GPS response = {res}")
        r = res.split(",")
        logging.debug(f"Timestamp = {r[0]}")
        logging.debug(f"Latitude  = {r[1]}")
        logging.debug(f"Longitude = {r[2]}\n")
    else:
        logging.error(f"{cmd} FAILED!")
        logging.error(f"returned {response}")
        return False

    # switch OFF GNSS
    status, cmd, response = self.AT_QGPS_END()
    if status:
        logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    # set priority back to WWAN
    status, cmd, response = self.AT_QGPSCFG_PRIO(gnss_prio=1)
    if status:
        logging.debug(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    return True
  
############################################################################################################
# DATA LINK LAYER FUNCTIONS
############################################################################################################

  def run_modem_general_at_commands(self):
    status = self.AT()
    # check if modem is alive
    if status:
        logging.info(f"PASSED!")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    status, cmd, response = self.ATI()
    # request product information
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    status, cmd, response = self.ATE(True)
    # turn on echo
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    status, cmd, response = self.AT_GSN()
    # request IMEI
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    status, cmd, response = self.AT_CCLK_REQUEST()
    # request current time
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    status, cmd, response = self.AT_QTEMP()
    # request silicon temperatures
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    return True

############################################################################################################
# NETWORK LAYER FUNCTIONS
############################################################################################################

  def connect_modem_to_network(self):
    # make sure to be disconnected first
    status, cmd = self.AT_CFUN(0)
    if status:
        logging.info(f"{cmd} PASSED!")

    # connect to network
    status, cmd = self.AT_CFUN(1)
    if status:
        logging.info(f"{cmd} PASSED!")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    # wait for network registration
    response = 0
    while response != 1:
        status, cmd, response = self.AT_CREG()
        # logging.info(f"{cmd} response = {response}")
        time.sleep(.25)
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    # wait for proper signal strength
    NO_SIGNAL = 99
    response = NO_SIGNAL
    while response == NO_SIGNAL:
        status, cmd, response = self.AT_CSQ()
        time.sleep(.25)    
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    return True

  def disconnect_modem_from_network(self):
    status, cmd = self.AT_CFUN(0)
    if status:
        logging.info(f"{cmd} PASSED!")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    return True

  def request_network_info(self):
    status, cmd, response = self.AT_CGEREP_REQUEST()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    status, cmd, response = self.AT_CGATT_REQUEST()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    status, cmd, response = self.AT_QCSQ()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    status, cmd, response = self.AT_CIMI_REQUEST()
    # request IMSI, only valid after CFUN=1
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    status, cmd, response = self.AT_QCCID_REQUEST()
    # request CCID
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    status, cmd, response = self.AT_CGDCONT_REQUEST()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False
    
    status, cmd, response = self.AT_CGACT_REQUEST()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False
    
    status, cmd, response = self.AT_CGPADDR_REQUEST()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    status, cmd, response = self.AT_CGREG_REQUEST()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    status, cmd, response = self.AT_CGEREP_REQUEST()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False
    
    status, cmd, response = self.AT_COPS_REQUEST()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    status, cmd, response = self.AT_QNWINFO()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    return True

  def run_modem_IP_commands(self):
    status, cmd, response = self.AT_QPING()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    status, cmd, response = self.AT_QNTP()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
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
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False, None

    status, cmd, response = self.AT_QHTTPCFG_SSLCTXID()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False, None

    status, cmd, response = self.AT_QSSLCFG_SSLVERSION()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False, None

    status, cmd, response = self.AT_QSSLCFG_CIPHERSUITE()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False, None

    status, cmd, response = self.AT_QSSLCFG_SECLEVEL()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
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
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

    status, cmd, response = self.AT_QIACT_REQUEST()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False

  def HTTP_GET(self, url):
    status, cmd, response = self.AT_QHTTPURL(url)
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False, None

    status, cmd, response = self.AT_QHTTPGET()
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False, None

    status, cmd, response = self.AT_QHTTPREAD()
    if status:
        logging.info(f"{cmd} PASSED!")
    else:
        logging.error(f"{cmd} FAILED!")
        return False, None

    return True, response

  def HTTP_POST(self, url, body):
    status, cmd, response = self.AT_QHTTPURL(url)
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False, None

    status, cmd, response = self.AT_QHTTPPOST(body)
    if status:
        logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
        logging.error(f"{cmd} FAILED!")
        return False, None

    status, cmd, response = self.AT_QHTTPREAD()
    if status:
        logging.info(f"{cmd} PASSED!")
    else:
        logging.error(f"{cmd} FAILED!")
        return False, None

    return True, response

  def HTTPS_GET(self, url):
    status, response = self.TLS_SETUP()
    if status:
        logging.info(f"TLS_SETUP PASSED! with response:\n{response}")
    else:
        logging.error(f"TLS_SETUP FAILED!")
        return False, None

    # run_modem_HTTP_commands()
    
    status, response = self.HTTP_GET(url)
    if status:
        logging.info(f"HTTP_GET PASSED! with response:\n{response}")
    else:
        logging.error(f"HTTP_GET FAILED!")
        return False, None

    return status, response

  def HTTPS_POST(self, url, body):
    status, response = self.TLS_SETUP()
    if status:
        logging.info(f"TLS_SETUP PASSED! with response:\n{response}")
    else:
        logging.error(f"TLS_SETUP FAILED!")
        return False, None

    # run_modem_HTTP_commands()

    status, response = self.HTTP_POST(url, body)
    if status:
        logging.info(f"HTTP_POST PASSED! with response:\n{response}")
    else:
        logging.error(f"HTTP_POST FAILED!")
        return False, None

    return status, response

if __name__ == "__main__":
  # https://realpython.com/python-logging/ ; levels are DEBUG, INFO, WARNING, ERROR, CRITICAL
  logging.basicConfig(format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S', level=logging.DEBUG)

  my_bg95 = osi_layer(logging)

  my_timer = timer(logging)

  logging.debug("\n******************************")

  if not my_bg95.open_usb():
    print("FAILED TO OPEN USB CONNECTION")
    exit()

  my_bg95.run_modem_GNSS_commands()

  my_bg95.run_modem_general_at_commands()

  # ##### START TIMER
  my_timer.start()

  my_bg95.connect_modem_to_network()
  my_bg95.request_network_info()

  # ##### READ TIMER
  my_timer.time_passed()

  my_bg95.run_modem_IP_commands()

  # ##### READ TIMER
  my_timer.time_passed()

  my_bg95.run_modem_HTTP_commands()

  status, response = my_bg95.HTTPS_GET("https://postman-echo.com/get/?foo1=bar1")
  if status:
    logging.info(f"HTTP GET PASSED! with response:\n{response}")
  else:
    logging.error(f"HTTP GET FAILED!")

  status, response = my_bg95.HTTPS_POST("https://postman-echo.com/post/", "foo1=bar1")
  if status:
    logging.info(f"HTTP POST PASSED! with response:\n{response}")
  else:
    logging.error(f"HTTP POST FAILED!")

  # ##### READ TIMER
  my_timer.time_passed()

  my_bg95.disconnect_modem_from_network()
  
  my_bg95.close_usb()

  logging.debug("\n******************************")
