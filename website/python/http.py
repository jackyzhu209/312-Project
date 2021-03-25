# creates html response
def html_header(filename):
    f = open(filename, 'r')
    html = f.read()
    header = "HTTP/1.1 200 OK\r\n"
    header += "Content-Type: text/html\r\n"
    header += "Content-Length: " + str(len(html)) + "\r\n"
    header += "X-Content-Type-Options: nosniff\r\n\r\n" 
    header += html
    f.close()
    return header.encode()

# creates javascript response
def js_header(filename):
    f = open(filename, 'r')
    js = f.read()
    header = "HTTP/1.1 200 OK\r\n"
    header += "Content-Type: text/javascript\r\n"
    header += "Content-Length: " + str(len(js)) + "\r\n"
    header += "X-Content-Type-Options: nosniff\r\n\r\n"
    header += js
    f.close()
    return header.encode()

# creates css response
def css_header(filename):
    f = open(filename, 'r')
    css = f.read()
    header = "HTTP/1.1 200 OK\r\n"
    header += "Content-Type: text/css\r\n"
    header += "Content-Length: " + str(len(css)) + "\r\n"
    header += "X-Content-Type-Options: nosniff\r\n\r\n"
    header += css
    f.close()
    return header.encode()

# creates image response
def image_header(filename, f_type):
    f = open(filename, 'rb')
    image = f.read()
    length = len(image)
    header = f"HTTP/1.1 200 OK\r\nContent-Type: image/{f_type}\r\nContent-Length: {length}\r\nX-Content-Type-Options: nosniff\r\n\r\n"
    head = header.encode() + image
    f.close()
    return head

# creates 301 response
def redirect(path):
    header = "HTTP/1.1 301 Moved Permanently\r\n"
    header += "Location: " + path
    return header.encode()

# creates not found response
def not_found():
    header = "HTTP/1.1 404 Not Found\r\n"
    header += "Content-Type: text/plain\r\n"
    header += "Content-Length: 36\r\n"
    header += "\r\nThe requested content does not exist"
    return header.encode()