import time
import serial
import logging
from timer import timer
from bg95_serial import bg95_serial
from bg95_atcmds import bg95_atcmds

# https://realpython.com/python-logging/ ; levels are DEBUG, INFO, WARNING, ERROR, CRITICAL
logging.basicConfig(format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S', level=logging.INFO)



############################################################################################################
# MISC SUPPORT FUNCTIONS
############################################################################################################

def modem_run_general_at_commands():
  status = my_bg95.AT()
  if status:
    logging.info(f"PASSED!")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.ATI()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.ATE(True)
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_GSN()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_CCLK_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  # status, cmd, response = my_bg95.AT_V()
  # if status:
    # logging.info(f"{cmd} PASSED! with response:\n{response}")
  # else:
  #   logging.info(f"{cmd} FAILED!")
  #   return False

  return True

def modem_connect_to_network():
  status, cmd = my_bg95.AT_CFUN(0)
  if status:
    logging.info(f"{cmd} PASSED!")

  status, cmd = my_bg95.AT_CFUN(1)
  if status:
    logging.info(f"{cmd} PASSED!")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_CGEREP_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  response = 0
  while response != 1:
    status, cmd, response = my_bg95.AT_CREG()
    time.sleep(.1)
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_CGATT_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  NO_SIGNAL = 99
  response = NO_SIGNAL
  while response == NO_SIGNAL:
    status, cmd, response = my_bg95.AT_CSQ()
    time.sleep(.1)    
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_CGDCONT_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_CGPADDR_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_CGEREP_REQUEST()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  return True

def modem_run_GNSS_commands():
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
    logging.info(f"{cmd} FAILED!")
    logging.info(f"returned {response}")
    return False

  # switch OFF GNSS
  status, cmd, response = my_bg95.AT_QGPS_END()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  # set priority back to WWAN
  status, cmd, response = my_bg95.AT_QGPSCFG_PRIO(gnss_prio=1)
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.error(f"{cmd} FAILED!")
    return False

def modem_run_IP_commands():
  status, cmd, response = my_bg95.AT_QPING()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_QNTP()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  return True

def modem_run_HTTP_commands():
  status, cmd, response = my_bg95.AT_QHTTPCFG()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  status, cmd, response = my_bg95.AT_QIACT()
  if status:
    logging.info(f"{cmd} PASSED! with response:\n{response}")
  else:
    logging.info(f"{cmd} FAILED!")
    return False

  return True

def modem_disconnect_from_network():
  status, cmd = my_bg95.AT_CFUN(0)
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
  my_bg95 = bg95_atcmds(logging)
  my_timer = timer(logging)

  logging.debug("\n******************************")

  if not my_bg95.open_usb():
    print("FAILED TO OPEN USB CONNECTION")
    exit()

  modem_run_general_at_commands()

  # modem_run_GNSS_commands()

  ##### START TIMER
  my_timer.start()

  modem_connect_to_network()

  ##### READ TIMER
  my_timer.time_passed()

  # modem_run_IP_commands()

  ##### READ TIMER
  my_timer.time_passed()

  modem_run_HTTP_commands()

  ##### READ TIMER
  my_timer.time_passed()

  modem_disconnect_from_network()
  
  my_bg95.close_usb()

  logging.debug("\n******************************")
