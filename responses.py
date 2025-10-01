import os
import socket
import time
from wsgiref.handlers import format_date_time


def sendHttpRes(
    conn: socket.socket,
    status_code: int,
    status: str,
    content_type: str,
    body: str,
    headers: dict,
    version: str = "1.1",
    isBinary: bool = False,
):
    current_rfc7231_time = format_date_time(time.time())
    content_length = len(body) if isBinary else len(body.encode())

    header_lines = [
        f"HTTP/{version} {status_code} {status}",
        f"Content-Type: {content_type}",
        f"Content-Length: {content_length}",
        f"Date: {current_rfc7231_time}",
        "Server: Multi-threaded HTTP Server",
    ]
    for key, value in headers.items():
        header_lines.append(f"{key}: {value}")

    response_headers = '\r\n'.join(header_lines) + '\r\n\r\n'
    response_bytes = response_headers.encode()
    
    if isBinary:
        body_bytes = body  
    else:
        body_bytes = body.encode()
    
    conn.sendall(response_bytes + body_bytes)


def sendHttpHtml(conn: socket.socket, file_path: str):
    content = ""
    with open(file_path, "r") as file:
        content = file.read()

    sendHttpRes(
        conn,
        status_code=200,
        status="OK",
        content_type="text/html; charset=utf-8",
        body=content,
        headers={},
    )


def sendHttpBin(conn: socket.socket, file_path: str):
    try:
        with open(file_path, "rb") as file:
            content = file.read()

        file_name = os.path.basename(file_path)
        sendHttpRes(
            conn,
            status_code=200,
            status="OK",
            content_type="application/octet-stream",
            body=content,
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"',
                "Connection": "keep-alive",
            },
            isBinary=True,
        )
    except Exception as e:
        raise e


def sendHttp500(conn: socket.socket):
    content = ""
    # Load the error page template from file
    with open("./errorpages/500.html", "r") as file:
        content = file.read()
    # Send the error response with appropriate status code and content
    sendHttpRes(
        conn,
        status_code=500,
        status="Internal Server Error",
        content_type="text/html; charset=utf-8",
        body=content,
        headers={},
    )


def sendHttp400(conn: socket.socket):
    content = ""
    with open("./errorpages/400.html", "r") as file:
        content = file.read()
    # Send the error response indicating the requested resource was not found
    sendHttpRes(
        conn,
        status_code=400,
        status="Not Found",
        content_type="text/html; charset=utf-8",
        body=content,
        headers={},
    )


def sendHttp404(conn: socket.socket):
    content = ""
    with open("./errorpages/404.html", "r") as file:
        content = file.read()
    # Send the error response indicating the requested resource was not found
    sendHttpRes(
        conn,
        status_code=404,
        status="Not Found",
        content_type="text/html; charset=utf-8",
        body=content,
        headers={},
    )


def sendHttp403(conn: socket.socket):
    content = ""
    with open("./errorpages/403.html", "r") as file:
        content = file.read()
    # Send forbidden response indicating access is not allowed
    sendHttpRes(
        conn,
        status_code=403,
        status="Forbidden",
        content_type="text/html; charset=utf-8",
        body=content,
        headers={},
    )


def sendHttp405(conn: socket.socket):
    content = ""
    with open("./errorpages/405.html", "r") as file:
        content = file.read()
    # Send method not allowed response
    sendHttpRes(
        conn,
        status_code=405,
        status="Method Not Allowed",
        content_type="text/html; charset=utf-8",
        body=content,
        headers={},
    )


def sendHttp415(conn: socket.socket):
    content = ""
    with open("./errorpages/415.html", "r") as file:
        content = file.read()
    # Send method not allowed response
    sendHttpRes(
        conn,
        status_code=415,
        status="Unsupported Media Type",
        content_type="text/html; charset=utf-8",
        body=content,
        headers={},
    )
