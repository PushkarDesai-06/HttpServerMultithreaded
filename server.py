import socket
import sys
import os

sock = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

args = sys.argv
