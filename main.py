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

def send_message_via_http_get():
  total_time_http_get = 0
  my_timer.start()
  status, response = my_bg95.HTTP_GET("http://postman-echo.com/get/?foo1=bar1")
  total_time_http_get += my_timer.time_passed()
  logging.info(f"Average time http_get: {total_time_http_get/(i+1)} seconds")
  if status:
    logging.info(f"HTTP_GET PASSED! with response:\n{response["result"]}\n===payload start===\n{response["payload"]}\n===payload end===")
  else:
    logging.error(f"HTTP_GET FAILED!")

def send_message_via_https_get():
  total_time_https_get = 0
  my_timer.start()
  status, response = my_bg95.HTTPS_GET("https://postman-echo.com/get/?foo1=bar1")
  total_time_https_get += my_timer.time_passed()
  logging.info(f"Average time https_get: {total_time_https_get/(i+1)} seconds")
  if status:
    logging.info(f"HTTPS_GET PASSED! with response:\n{response["result"]}\n===payload start===\n{response["payload"]}\n===payload end===")
  else:
    logging.error(f"HTTPS_GET FAILED!")

def send_message_via_http_post():
  total_time_http_post = 0
  my_timer.start()
  status, response = my_bg95.HTTP_POST("http://postman-echo.com/post/", "foo1=bar1")
  total_time_http_post += my_timer.time_passed()
  logging.info(f"Average time http_post: {total_time_http_post/(i+1)} seconds")
  if status:
    logging.info(f"HTTP_POST PASSED! with response:\n{response["result"]}\n===payload start===\n{response["payload"]}\n===payload end===")
  else:
    logging.error(f"HTTP_POST FAILED!")

def send_message_via_https_post():
  total_time_https_post = 0
  my_timer.start()
  status, response = my_bg95.HTTPS_POST("https://postman-echo.com/post/", "foo1=bar1")
  total_time_https_post += my_timer.time_passed()
  logging.info(f"Average time https_post: {total_time_https_post/(i+1)} seconds")
  if status:
    logging.info(f"HTTPS_POST PASSED! with response:\n{response["result"]}\n===payload start===\n{response["payload"]}\n===payload end===")
  else:
    logging.error(f"HTTPS_POST FAILED!")

if __name__ == "__main__":
  my_timer = timer(logging)

  logging.debug("\n******************************")

  if not my_bg95.open_usb():
    print("FAILED TO OPEN USB CONNECTION")
    exit()

  my_bg95.connect_modem_to_network()

  for i in range(365):
    logging.info(f"***** Loop {i}")

    my_bg95.request_network_info()

    send_message_via_http_get()
    time.sleep(1)
    send_message_via_https_get()
    time.sleep(1)
    send_message_via_http_post()
    time.sleep(1)
    send_message_via_https_post()
    time.sleep(10) 

  my_bg95.disconnect_modem_from_network()

  my_bg95.close_usb()

  logging.debug("\n******************************")
 