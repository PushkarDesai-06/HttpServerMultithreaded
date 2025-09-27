from concurrent.futures import ThreadPoolExecutor
import re
import socket
import sys
import os
import logging
import threading
import time
from wsgiref.handlers import format_date_time

from responses import sendHttp403
from utils import parseHttp


class HTTPServer:

    def __init__(self, host="127.0.0.1", port=8080, max_threads=10):
        self.host = host
        self.port = port
        self.max_threads = max_threads
        self.thread_pool = ThreadPoolExecutor(max_workers=max_threads)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        logging.basicConfig(filename="./logfile.log")

    def start(self):
        socket.bind((self.host, self.port))
        print(f"Server bound to {self.host} on port: {self.port}")
        print("Press Ctrl + C to exit")
        while True:
            try:
                conn, addr = socket.accept()
                self.thread_pool.submit(self.handleClient, conn, addr)
            except Exception as e:
                print(e)
                socket.close()

    def handleClient(self, conn: socket.socket, addr: str):
        try:
            threadName = threading.current_thread().name
            print(f"{threadName}-> Connection from {addr}")
            while True:
                data = conn.recv(1024)
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
                    self.sendHttp400(conn)  # Bad request
                    conn.close()
                    return
                
                request = parseHttp(data)
                print(f"{threadName}-> Request: {request.req_type} {request.req_path} {request.req_version}")
                allowed_hosts = [f'{self.host}:{self.port}']
                
                if request.headers.host == "":
                    self.sendHttp400(conn)
                    conn.close()
                    return
                if request.headers.host not in allowed_hosts:
                    sendHttp403(conn)
                    conn.close()
                    return 
                
                if request.req_path == "/":
                    request.req_path = "/index.html"  # Default file
                # Remove starting slash and join with resources
                clean_path = request.req_path.lstrip("/")
                joined_path = os.path.join("resources", clean_path)
                file_path = os.path.normpath(joined_path)
                print(f"{threadName}-> File path: {file_path}")
                # Security check - ensuring path stays within resources directory
                if (
                    not file_path.startswith("resources" + os.sep)
                    and file_path != "resources"
                ):
                    print(f"{threadName}-> Path traversal attempt detected")
                    self.sendHttp403(conn)
                elif request.req_type != "GET" or request.req_type != "POST":
                    self.sendHttp405(conn)
                elif not os.path.exists(file_path):
                    print(f"{threadName}-> File not found")
                    self.sendHttp404(conn)
                elif os.path.isdir(file_path):
                    print(f"{threadName}-> Directory access not allowed")
                    self.sendHttp403(conn)
                else:
                    try:
                        with open(file_path, "r", encoding="utf-8") as file:
                            content = file.read()
                        # Determine content type based on file extension
                        allowed_extensions = ['.html' , '.txt' , '.png' , '.jpg' , '.jpeg']
                        _, ext = os.path.splitext(file_path)
                        if ext not in allowed_extensions :
                            self.sendHttp415(conn)
                        content_type = "text/html; charset=utf-8"
                        if ext != ".html":
                            content_type = "application/octet-stream"
                        self.sendHttpRes(
                            conn,
                            status_code=200,
                            status="OK",
                            content_type=content_type,
                            body=content,
                        )
                        print(f"{threadName}-> File served successfully")
                    except (IOError, OSError) as e:
                        print(f"{threadName}-> Error reading file: {e}")
                        self.sendHttp500(conn)
                if (request.headers.connection == "close") or ((request.headers.connection == "") and request.req_version == "HTTP/1.0"): #check for connection to clise the connection 
                    conn.close()
                    break    
        except Exception as e:
            print(f"{threadName}-> Error serving request {e}")
            conn.close()

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
            headers = {"connection" : ''}
            for line in lines:
                if line == "": #empty line
                    break
                key, value = line.split(":")
                value = value.removeprefix(" ")
                headers[key] = value
            request_object["headers"] = headers
            body_lines = request.split("\r\n\r\n")[1]
            body = {}
            if request_object["req_type"] == "application/json":
                for line in body_lines.split("\r\n"):
                    key, value = line.split(":")
                    value = value.removeprefix(" ")
                    body[key] = value
            request_object["body"] = body
            return request_object
        except Exception as e:
            raise e

    def sendHttpRes(
        conn: socket.socket,
        status_code: int,
        status: str,
        content_type: str,
        body: str,
        headers: dict,
    ):
        current_rfc7231_time = format_date_time(time.time())
        # Construct the HTTP response following HTTP/1.1 protocol
        response = f"""
        HTTP/1.1 {status_code} {status}
        Content-Type: {content_type}
        Content-Length: {len(body.encode("utf-8"))}
        Date: {current_rfc7231_time}
        Server: Multi-threaded HTTP Server
        {[f"{key}: {value}" for key , value in headers].join('\n')}
        
        {body}"""
        # Send the response as bytes over the socket connection
        conn.send(response.encode())

    def sendHttpHtml(self , conn : socket.socket , file_path : str):
        
        content = ''
        with open(file_path , "r") as file:
            content = file.read()
        
        self.sendHttpRes(
            conn,
            status_code=200,
            status="OK",
            content_type="text/html; charset=utf-8",
            body=content,
        )

    # def

    def sendHttp500(self, conn: socket.socket):
        content = ""
        # Load the error page template from file
        with open("errorpages/500.html", "r") as file:
            content = file.read()
        # Send the error response with appropriate status code and content
        self.sendHttpRes(
            conn,
            status_code=500,
            status="Internal Server Error",
            content_type="text/html; charset=utf-8",
            body=content,
        )

    def sendHttp400(self, conn: socket.socket):
        content = ""
        with open("./errorpages/400.html", "r") as file:
            content = file.read()
        # Send the error response indicating the requested resource was not found
        self.sendHttpRes(
            conn,
            status_code=404,
            status="Not Found",
            content_type="text/html; charset=utf-8",
            body=content,
        )

    def sendHttp404(self, conn: socket.socket):
        content = ""
        with open("./errorpages/404.html", "r") as file:
            content = file.read()
        # Send the error response indicating the requested resource was not found
        self.sendHttpRes(
            conn,
            status_code=404,
            status="Not Found",
            content_type="text/html; charset=utf-8",
            body=content,
        )

    def sendHttp403(self, conn: socket.socket):
        content = ""
        with open("./errorpages/403.html", "r") as file:
            content = file.read()
        # Send forbidden response indicating access is not allowed
        self.sendHttpRes(
            conn,
            status_code=403,
            status="Forbidden",
            content_type="text/html; charset=utf-8",
            body=content,
        )

    def sendHttp405(self, conn: socket.socket):
        content = ""
        with open("./errorpages/405.html", "r") as file:
            content = file.read()
        # Send method not allowed response
        self.sendHttpRes(
            conn,
            status_code=405,
            status="Method Not Allowed",
            content_type="text/html; charset=utf-8",
            body=content,
        )
    
    def sendHttp415(self, conn: socket.socket):
        content = ""
        with open("./errorpages/415.html", "r") as file:
            content = file.read()
        # Send method not allowed response
        self.sendHttpRes(
            conn,
            status_code=415,
            status="Unsupported Media Type",
            content_type="text/html; charset=utf-8",
            body=content,
        )
        
