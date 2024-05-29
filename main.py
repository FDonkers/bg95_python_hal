import logging
import time
from timer import timer
from bg95_osi_layer import osi_layer

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


  total_time_http_get = 0
  total_time_https_get = 0
  total_time_http_post = 0
  total_time_https_post = 0
  for i in range(500):
    logging.info(f"***** Loop {i}")

    my_bg95.connect_modem_to_network()
    # my_bg95.request_network_info()

    # ##### HTTP_GET
    # my_timer.start()
    # status, response = my_bg95.HTTP_GET("http://postman-echo.com/get/?foo1=bar1")
    # total_time_http_get += my_timer.time_passed()
    # logging.info(f"Average time http_get: {total_time_http_get/(i+1)} seconds")
    # if status:
    #   logging.info(f"HTTP(S)_GET/POST PASSED! with response:\n{response["result"]}\n===payload start===\n{response["payload"]}\n===payload end===")
    # else:
    #   logging.error(f"HTTP(S)_GET/POST FAILED!")

    # time.sleep(1)

    ##### HTTPS_GET
    # my_timer.start()
    # status, response = my_bg95.HTTPS_GET("https://postman-echo.com/get/?foo1=bar1")
    # total_time_https_get += my_timer.time_passed()
    # logging.info(f"Average time https_get: {total_time_https_get/(i+1)} seconds")
    # if status:
    #   logging.info(f"HTTP(S)_GET/POST PASSED! with response:\n{response["result"]}\n===payload start===\n{response["payload"]}\n===payload end===")
    # else:
    #   logging.error(f"HTTP(S)_GET/POST FAILED!")

    # time.sleep(1)

    ##### HTTP_POST
    # my_timer.start()
    # status, response = my_bg95.HTTP_POST("http://postman-echo.com/post/", "foo1=bar1")
    # total_time_http_post += my_timer.time_passed()
    # logging.info(f"Average time http_post: {total_time_http_post/(i+1)} seconds")
    # if status:
    #   logging.info(f"HTTP(S)_GET/POST PASSED! with response:\n{response["result"]}\n===payload start===\n{response["payload"]}\n===payload end===")
    # else:
    #   logging.error(f"HTTP(S)_GET/POST FAILED!")

    # time.sleep(1)

    ##### HTTPS_POST
    my_timer.start()
    status, response = my_bg95.HTTPS_POST("https://postman-echo.com/post/", "foo1=bar1")
    total_time_https_post += my_timer.time_passed()
    logging.info(f"Average time https_post: {total_time_https_post/(i+1)} seconds")
    if status:
      logging.info(f"HTTP(S)_GET/POST PASSED! with response:\n{response["result"]}\n===payload start===\n{response["payload"]}\n===payload end===")
    else:
      logging.error(f"HTTP(S)_GET/POST FAILED!")

    my_bg95.disconnect_modem_from_network()

    time.sleep(100)

  # ##### READ TIMER

  my_bg95.close_usb()

  logging.debug("\n******************************")
