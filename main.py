import logging
from timer import timer
from osi_layer import osi_layer

# https://realpython.com/python-logging/ ; levels are DEBUG, INFO, WARNING, ERROR, CRITICAL
logging.basicConfig(format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

############################################################################################################
# MAIN
############################################################################################################

my_bg95 = osi_layer(logging)

if __name__ == "__main__":
  my_timer = timer(logging)

  logging.debug("\n******************************")

  if not my_bg95.open_usb():
    print("FAILED TO OPEN USB CONNECTION")
    exit()

  # my_bg95.run_modem_GNSS_commands()

  # my_bg95.run_modem_general_at_commands()

  # ##### START TIMER
  # my_timer.start()

  my_bg95.connect_modem_to_network()
  # my_bg95.request_network_info()

  # ##### READ TIMER
  # my_timer.time_passed()

  # my_bg95.run_modem_IP_commands()

  # ##### READ TIMER
  # my_timer.time_passed()

  # my_bg95.run_modem_HTTP_commands()

  # NO TLS

  # status, response = my_bg95.HTTP_GET("http://postman-echo.com/get/?foo1=bar1")
  # if status:
  #   logging.info(f"HTTP_POST PASSED! with response:\n{response["result"]}\n===payload start===\n{response["payload"]}\n===payload end===")
  # else:
  #   logging.error(f"HTTP_GET FAILED!")

  # status, response = my_bg95.HTTP_POST("http://postman-echo.com/post/", "foo1=bar1")
  # if status:
  #   logging.info(f"HTTP_POST PASSED! with response:\n{response["result"]}\n===payload start===\n{response["payload"]}\n===payload end===")
  # else:
  #   logging.error(f"HTTP_POST FAILED!")

  # with TLS

  status, response = my_bg95.HTTPS_GET("https://postman-echo.com/get/?foo1=bar1")
  if status:
    logging.info(f"HTTPS_GET PASSED! with response:\n{response["result"]}\n===payload start===\n{response["payload"]}\n===payload end===")
  else:
    logging.error(f"HTTPS_GET FAILED!")

  # status, response = my_bg95.HTTPS_POST("https://postman-echo.com/post/", "foo1=bar1")
  # if status:
  #   logging.info(f"HTTPS_POST PASSED! with response:\n{response["result"]}\n===payload start===\n{response["payload"]}\n===payload end===")
  # else:
  #   logging.error(f"HTTPS_POST FAILED!")

  # ##### READ TIMER
  # my_timer.time_passed()

  # my_bg95.disconnect_modem_from_network()
  
  my_bg95.close_usb()

  logging.debug("\n******************************")
