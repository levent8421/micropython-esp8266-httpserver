import network
import time
import log
import conf
import led

wlan = None

def init_wifi():
  global wlan
  wifi_conf = conf.get('wifi')
  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  wlan.disconnect()
  log.log('Connect to ', wifi_conf['ssid'], wifi_conf['password'])
  wlan.connect(wifi_conf['ssid'], wifi_conf['password'])
  while (wlan.ifconfig()[0] == '0.0.0.0'):
    time.sleep(0.5)
    log.log('Waiting for wifi connection...')
    led.status_led.switch()
  log.log('Wifi connect success!')
  led.status_led.on()
  return True

def connect():
  init_wifi()


