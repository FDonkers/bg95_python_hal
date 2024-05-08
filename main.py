import time
import logging
from timer import timer
from bg95_atcmds import bg95_atcmds

# https://realpython.com/python-logging/ ; levels are DEBUG, INFO, WARNING, ERROR, CRITICAL
logging.basicConfig(format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

############################################################################################################
# MISC HIGH LEVEL FUNCTIONS
############################################################################################################

def run_modem_general_at_commands():
  status = my_bg95.AT()
  # check if modem is alive
  if status:
    logging.info(f"PASSED!")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.ATI()
  # request product information
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.ATE(True)
  # turn on echo
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_GSN()
  # request IMEI
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_CCLK_REQUEST()
  # request current time
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_QTEMP()
  # request silicon temperatures
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  return True

def disconnect_modem_from_network():
  status, cmd = my_bg95.AT_CFUN(0)
  if status:
    logging.info(f"{cmd} PASSED!")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  return True

def connect_modem_to_network():
  # make sure to be disconnected first
  status, cmd = my_bg95.AT_CFUN(0)
  if status:
    logging.info(f"{cmd} PASSED!")

  # connect to network
  status, cmd = my_bg95.AT_CFUN(1)
  if status:
    logging.info(f"{cmd} PASSED!")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  # wait for network registration
  response = 0
  while response != 1:
    status, cmd, response = my_bg95.AT_CREG()
    time.sleep(.1)
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  # wait for proper signal strength
  NO_SIGNAL = 99
  response = NO_SIGNAL
  while response == NO_SIGNAL:
    status, cmd, response = my_bg95.AT_CSQ()
    time.sleep(.1)    
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  return True


def request_network_info():
  status, cmd, response = my_bg95.AT_CGEREP_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_CGATT_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_QCSQ()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_CIMI_REQUEST()
  # request IMSI, only valid after CFUN=1
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_QCCID_REQUEST()
  # request CCID
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_CGDCONT_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False
  
  status, cmd, response = my_bg95.AT_CGACT_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False
  
  status, cmd, response = my_bg95.AT_CGPADDR_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_CGREG_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_CGEREP_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False
  
  status, cmd, response = my_bg95.AT_COPS_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_QNWINFO()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  return True

def run_modem_GNSS_commands():
  #ToDo: add 'assisted GNSS' commands, e.g. XTRA file download, etc

  # set priority to GNSS
  status, cmd, response = my_bg95.AT_QGPSCFG_PRIO(gnss_prio=0)
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  # check if GNSS is already ON
  status, cmd, response = my_bg95.AT_QGPS_STATUS_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
    status, urc = bg95_atcmds.extract_urc(response, "+QGPS")
    gps_on = (urc[0] == '1')
    logging.info(f"GPS is ON") if (gps_on == True) else logging.info(f"GPS is OFF")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  # switch ON GNSS if not already ON  
  if not gps_on:
    status, cmd, response = my_bg95.AT_QGPS_ON()
    if status:
      logging.info(f"{cmd} PASSED! with response:\n{response}")
    else:
      logging.error(f"{cmd} FAILED!")
      return False

  # check if GNSS is indeed switched ON
  status, cmd, response = my_bg95.AT_QGPS_STATUS_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
    status, urc = bg95_atcmds.extract_urc(response, "+QGPS")
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
    status, cmd, response = my_bg95.AT_QGPSLOC_REQUEST()
    if status:
      # check if fix is obtained
      s, urc = bg95_atcmds.extract_urc(response, "+CME ERROR")
      got_fix = (urc == None)

  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
    status, res = bg95_atcmds.extract_urc(response, "+QGPSLOC")
    logging.info(f"GPS response = {res}")
    r = res.split(",")
    logging.info(f"Timestamp = {r[0]}")
    logging.info(f"Latitude  = {r[1]}")
    logging.info(f"Longitude = {r[2]}\n")
  else:
    logging.error(f"{cmd} FAILED!")
    logging.error(f"returned {response}")
    return False

  # switch OFF GNSS
  status, cmd, response = my_bg95.AT_QGPS_END()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  # set priority back to WWAN
  status, cmd, response = my_bg95.AT_QGPSCFG_PRIO(gnss_prio=1)
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

def run_modem_IP_commands():
  status, cmd, response = my_bg95.AT_QPING()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_QNTP()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  return True

def run_modem_HTTP_commands():
  status, cmd, response = my_bg95.AT_QHTTPCFG_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_QIACT_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

def HTTP_GET(url):
  status, cmd, response = my_bg95.AT_QHTTPURL(url)
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False, None

  status, cmd, response = my_bg95.AT_QHTTPGET()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False, None

  status, cmd, response = my_bg95.AT_QHTTPREAD()
  if status:
    logging.info(f"{cmd} PASSED!")
  else:
    logging.error(f"{cmd} FAILED!")
    return False, None

  return True, response

def HTTP_POST(url, body):
  status, cmd, response = my_bg95.AT_QHTTPURL(url)
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False, None

  status, cmd, response = my_bg95.AT_QHTTPPOST(body)
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False, None

  status, cmd, response = my_bg95.AT_QHTTPREAD()
  if status:
    logging.info(f"{cmd} PASSED!")
  else:
    logging.error(f"{cmd} FAILED!")
    return False, None

  return True, response

def HTTPS_GET(url):
  status, cmd, response = my_bg95.AT_QHTTPCFG_RESPONSEHEADER(True)
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False, None

  status, cmd, response = my_bg95.AT_QHTTPCFG_SSLCTXID()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False, None

  status, cmd, response = my_bg95.AT_QSSLCFG_SSLVERSION()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False, None

  status, cmd, response = my_bg95.AT_QSSLCFG_CIPHERSUITE()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False, None

  status, cmd, response = my_bg95.AT_QSSLCFG_SECLEVEL()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False, None

  run_modem_HTTP_commands()

  status, response = HTTP_GET(url)
  return status, response

def HTTPS_POST(url, body):
  status, cmd, response = my_bg95.AT_QHTTPCFG_RESPONSEHEADER(True)
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False, None

  status, cmd, response = my_bg95.AT_QHTTPCFG_SSLCTXID()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False, None

  status, cmd, response = my_bg95.AT_QSSLCFG_SSLVERSION()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False, None

  status, cmd, response = my_bg95.AT_QSSLCFG_CIPHERSUITE()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False, None

  status, cmd, response = my_bg95.AT_QSSLCFG_SECLEVEL()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False, None

  run_modem_HTTP_commands()

  status, response = HTTP_POST(url, body)
  return status, response

############################################################################################################
# MAIN
############################################################################################################
  
if __name__ == "__main__":
  my_bg95 = bg95_atcmds(logging)
  my_timer = timer(logging)

  logging.debug("\n******************************")

  if not my_bg95.open_usb():
    print("FAILED TO OPEN USB CONNECTION")
    exit()

  # run_modem_general_at_commands()

  # run_modem_GNSS_commands()

  ##### START TIMER
  my_timer.start()

  connect_modem_to_network()
  # request_network_info()

  ##### READ TIMER
  my_timer.time_passed()

  # run_modem_IP_commands()

  ##### READ TIMER
  my_timer.time_passed()

  # run_modem_HTTP_commands()

  status, response = HTTPS_GET("https://postman-echo.com/get/?foo1=bar1")
  if status:
    logging.info(f"HTTP GET PASSED! with response:\n{response}")
  else:
    logging.error(f"HTTP GET FAILED!")

  status, response = HTTPS_POST("https://postman-echo.com/post/", "foo1=bar1")
  if status:
    logging.info(f"HTTP GET PASSED! with response:\n{response}")
  else:
    logging.error(f"HTTP GET FAILED!")

  ##### READ TIMER
  my_timer.time_passed()

  disconnect_modem_from_network()
  
  my_bg95.close_usb()

  logging.debug("\n******************************")
