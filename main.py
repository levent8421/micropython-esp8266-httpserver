import log
import wifi
import server

def main():
  wifi.connect()
  server.start()

if __name__ == '__main__':
  main()


