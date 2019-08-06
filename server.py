import ure
import socket
import wifi
import socket
import log
import json
import led

MAX_REQUEST_SIZE = 1204
PORT = 80

class RequestHandler(object):
    def __init__(self):
        self.__handlers = {
            'GET': {},
            'POST': {},
            'DELETE': {},
            'PUT': {},
            'OPTION': {}
        }

    def register_handler(self, method, path, fn):
        if method in self.__handlers:
            self.__handlers[method][path] = fn
        else:
            raise Exception('Unknown method %s' % method)
            
    @staticmethod
    def try_read_file(path):
      if '?' in path:
        path = path.split('?')[0]
      try:
        with open(path) as f:
          return f.read()
      except:
        return None
        
    def __call__(self, *args, **kwargs):
        method = kwargs['method']
        url = kwargs['url']
        headers = kwargs['headers']
        body = kwargs['body']
        
        file_content = RequestHandler.try_read_file(url)
        if file_content:
          return '200 OK', file_content
        
        if method in self.__handlers:
            handlers = self.__handlers[method]
            if url in handlers:
                handler = handlers[url]
                resp = handler(method, url, headers, body)
                if type(resp) == '<class \'tuple\'>':
                    return resp
                else:
                    return '200 OK', resp
            else:
                return '404 NOT_FOUND', 'Page Not Found'
        else:
            return '405 METHOD_NOT_ALLOWED', 'Unknown method %s' % method


class WebServer(object):
    def __init__(self, host, wlan):
        self.__wlan = wlan
        self.__build_socket()
        self.__host = host

    def __build_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__sc = s

    def listen(self, port):
        self.__sc.bind((self.__host, port))
        self.__sc.listen(1)
        print('Server startup on [%s]:[%s]' % (self.__host, port))

    def accept(self, fn):
        while True:
            conn, addr = self.__sc.accept()
            try:
                data = conn.recv(MAX_REQUEST_SIZE)
                method, url, headers, body = self.http_unpack(data)
                status, resp = fn(url=url, headers=headers, body=body, method=method)
                conn.send(('HTTP/1.1 %s\r\n' % status).encode())
                conn.send(('Content-Length: %s\r\n' % len(resp)).encode())
                conn.send(b'\r\n')
                conn.send(resp.encode())
            except Exception as e:
                print(e)
            finally:
                conn.close()

    @staticmethod
    def http_unpack(data):
        lines = data.decode().split('\r\n')
        status_line = lines[0]
        method, url, version = WebServer.unpack_status_line(status_line)
        print('Resolve request [%s][%s][%s]' % (method, url, version))

        headers, line_num = WebServer.unpack_headers(lines[1::])
        if len(lines) > line_num + 2:
            body = lines[line_num + 2::]
        else:
            body = None
        return method, url, headers, body

    @staticmethod
    def unpack_status_line(status_line):
        res = ure.match(r'^(GET|POST|PUT|DELETE|OPTION)\s(.+)\s(.*)', status_line)
        method = res.group(1)
        url = res.group(2)
        try:
          version = res.group(3)
        except:
          version = None
        return method, url, version

    @staticmethod
    def unpack_headers(lines):
        headers = {}
        line_num = 0
        for line in lines:
            if len(line) == 0:
                break
            line_num += 1
            name_and_value = line.split(':')
            item_len = len(name_and_value)
            if item_len == 2:
                header_name = name_and_value[0]
                header_value = name_and_value[1]
            elif item_len > 2:
                header_name = name_and_value[0]
                header_value = name_and_value[1::]
            elif item_len == 1:
                header_name = name_and_value[0]
                header_value = None
            else:
                continue
            headers[header_name] = header_value
        return headers, line_num


def index(method, path, headers, body):
    return '[%s][%s]' % (method, path)


def start():
    wlan = wifi.wlan
    handler = RequestHandler()
    handler.register_handler('GET', '/', index)
    server = WebServer(wlan.ifconfig()[0], wlan)
    server.listen(PORT)
    server.accept(handler)


