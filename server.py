from concurrent.futures import ThreadPoolExecutor
import socket
import os
import logging
import sys
import threading
import responses as res

class HTTPServer:

    def __init__(self, host, port, max_threads):
        self._host = host
        self._port = port
        self._max_threads = max_threads
        self._thread_pool = ThreadPoolExecutor(max_workers=max_threads)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Prevents address already being used issue
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        logging.basicConfig(
            level=logging.DEBUG,  # Minimum level to capture
            format="[ %(asctime)s ] - %(levelname)s - %(message)s",
        )

    def start(self):
        try:
            self._socket.bind((self._host, self._port))
            self._socket.listen()
            logging.info(f"Server running on {self._host}:{self._port}")
            logging.info("Press Ctrl + C to exit")
            while True:
                try:
                    conn, addr = self._socket.accept()
                    self._thread_pool.submit(self.handleClient, conn, addr)
                except KeyboardInterrupt:
                    logging.info("Server shutting down...")
                    self._socket.close()
                except Exception as e:
                    logging.error(e)
                    self._socket.close()
                    return
        except Exception as e:
            logging.error(f"Could not start the server! Check input arguments. \nError: {e}")

    def handleClient(self, conn: socket.socket, addr: str):
        try:
            threadName = threading.current_thread().name
            logging.info(f"{threadName}-> Connection from {addr}")
            
            while True:
                data = conn.recv(8192)
                if not data:
                    conn.close()
                    return
                data = data.decode()
                lines = data.split("\r\n")
                if not lines or not lines[0]:
                    conn.close()
                    return
                first_line = lines[0].split(" ")
                if len(first_line) < 3:
                    logging.error("")
                    res.sendHttp400(conn)  # Bad request
                    conn.close()
                    return

                request = self.parseHttp(data)
                logging.info(
                    f"{threadName}-> Request: {request['req_type']} {request['req_path']} {request['req_version']}"
                )
                # Fix property access
                allowed_hosts = [f"{self._host}:{self._port}" , f"localhost:{self._port}"]

                if request['headers'].get('host', '') == "":
                    res.sendHttp400(conn)
                    conn.close()
                    return
                if request['headers'].get('host', '') not in allowed_hosts:
                    print(request['headers']['host'])
                    res.sendHttp403(conn)
                    conn.close()
                    return

                if request['req_path'] == "/":
                    request['req_path'] = "/index.html"  # Default file
                    res.sendHttpHtml(conn , file_path='./resources/index.html')
                    continue
                # Remove starting slash and join with resources
                clean_path = request['req_path'].lstrip("/")
                joined_path = os.path.join("resources", clean_path)
                file_path = os.path.normpath(joined_path)
                logging.info(f"{threadName}-> File path: {file_path}")
                # Security check - ensuring path stays within resources directory
                if (
                    not file_path.startswith("resources" + os.sep)
                    and not file_path == "resources"
                ):
                    logging.info(f"{threadName}-> Path traversal attempt detected")
                    res.sendHttp403(conn)
                # Fix logic error - should be 'and' not 'or'
                elif request['req_type'] != "GET" and request['req_type'] != "POST":
                    res.sendHttp405(conn)
                elif not os.path.exists(file_path):
                    logging.error(f"{threadName}-> File not found")
                    res.sendHttp404(conn)
                elif os.path.isdir(file_path):
                    logging.warning(f"{threadName}-> Directory access not allowed")
                    res.sendHttp403(conn)
                else:
                    try:
                        allowed_extensions = [".html", ".txt", ".png", ".jpg", ".jpeg"]
                        _, ext = os.path.splitext(file_path)
                        if ext not in allowed_extensions:
                            res.sendHttp415(conn)
                        elif ext == ".html":
                            res.sendHttpHtml(
                                conn,
                                file_path=file_path
                            )
                        else:
                            res.sendHttpBin(
                                conn,
                                file_path=file_path
                            )
                        logging.info(f"{threadName}-> File served successfully")
                    except (IOError, OSError) as e:
                        logging.info(f"{threadName}-> Error reading file: {e}")
                        res.sendHttp500(conn)
            
                if (request['headers'].get('connection', '') == "close") or (
                    (request['headers'].get('connection', '') == "")
                    and request['req_version'] == "HTTP/1.0"
                ):  # check for connection to close the connection
                    conn.close()
                    break
        except KeyboardInterrupt as e:
            conn.close()
            raise e
        except Exception as e:
            logging.error(f"{threadName}-> Error serving request {e}")

    def parseHttp(self, request: str):
        try:
            lines = request.split("\r\n")
            first_line = lines[0].split(" ")
            if len(first_line) < 3:
                raise Exception("Bad request")
            request_object = {}
            request_object["req_type"] = first_line[0]
            request_object["req_path"] = first_line[1]
            request_object["req_version"] = first_line[2]
            headers = {"connection": ""}
            for line in lines[1:]:
                if line == "":  # empty line
                    break
                key , value = line.split(": ")
                headers[key.lower()] = value.lower()
            request_object["headers"] = headers
            body_lines = request.split("\r\n\r\n")[1]
            body = {}
            if request_object["req_type"] == "application/json":
                for line in body_lines.split("\r\n"):
                    key, value = line.split(":")
                    value = value.removeprefix(" ")
                    body[key] = value
            request_object["body"] = body
            
            # !!!! debug
            # logging.debug(request_object)
            
            return request_object
        except Exception as e:
            logging.error(e)
            raise e

args = sys.argv
host = "127.0.0.1"
port = 8080
max_threads = 10

try:
    if len(args) > 1:
        port = int(args[1])
    if len(args) > 2:
        host = args[2]
    if len(args) > 3:
        max_threads = int(args[3])
except Exception as e:
    logging.error(e)

server = HTTPServer(host=host, port=port, max_threads=max_threads)
server.start()