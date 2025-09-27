import socket


def sendHttpRes(
    conn: socket.socket, status_code: int, status: str, content_type: str, body: str
):
    """
    Send a generic HTTP response with specified parameters.
    
    Args:
        conn: The socket connection to send the response through
        status_code: HTTP status code (e.g., 200, 404, 500)
        status: HTTP status message (e.g., "OK", "Not Found")
        content_type: MIME type of the response content
        body: The actual content/body of the response
    """
    # Construct the HTTP response following HTTP/1.1 protocol
    response = f"""
HTTP/1.1 {status_code} {status}
Content-Length: {len(body.encode("utf-8"))}
Content-Type: {content_type}

{body}"""
    # Send the response as bytes over the socket connection
    conn.send(response.encode())


def sendHttp500(conn: socket.socket):
    content = ""
    # Load the error page template from file
    with open("errorpages/500.html", "r") as file:
        content = file.read()
    # Send the error response with appropriate status code and content
    sendHttpRes(
        conn,
        status_code=500,
        status="Internal Server Error",
        content_type="text/html; charset=utf-8",
        body=content,
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
    )
