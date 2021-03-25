def parseRequest(socket, header, data):    
    path = header[0].split(" ")[1]

    #finds content length, boundary(will be turned into bytes if dealing with non-string bodies)
    content_length = header[1].split(": ")[1]
    body_length = 0
    boundary = header[2].split("boundary=")[1]
    boundary = "--" + boundary

    #checks for path
    if path = "/enternewuser":
        buffer = ""
        #of format user,pass,re-enter pass
        user = ""
        pwd = ""
        rePwd = ""
        data = data.decode()
        startedBody = False
        if "\r\n\r\n" in data:
            startBody = True
            body = data.split("\r\n\r\n")[1]
            body_length += len(body)
        while content_length > body_length:
            recvData = socket.request.recv(1024)
            if "\r\n\r\n" in data and startBody = False:
                startBody = True
                body = recvData.decode().split("\r\n\r\n")[1]
                body_length += len(body)
            else:
                body += recvData.decode()
                body_length += len(recvData.decode())
        #body now contains all received data
        bodySections = body.split(boundary)
        user = bodySections[0].split("\r\n\r\n")[1]
        pwd = bodySections[1].split("\r\n\r\n")[1]
        rePwd = bodySections[2].split("\r\n\r\n")[1]
        #remember to do something about pwd and repwd not being the same, ask adam/rachael
    elif path = "/"



