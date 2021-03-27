stringPaths = ["/enternewuser", ""]
def parseRequest(socket, header, data):
    retData = ()   
    path = header[0].split(" ")[1]

    #finds content length, boundary(will be turned into bytes if dealing with non-string bodies)
    content_length = 0
    body_length = 0
    boundary = ""
    
    for headers in header:
        if "boundary=" in headers:
            boundary = headers.split("boundary=")[1]
            boundary = "--" + boundary
        elif "Content-Length:" in headers:
            content_length = int(headers.split("Content-Length: ")[1])

    #checks for path, rest of the body is essentially grabbing the splitting by the boundary and grabbing the actual values
    if path == "/enternewuser" or path == "/loginuser" or path == "/comment":
        buffer = ""
        #of format user,pass,re-enter pass        
        data = data.decode()
        startedBody = False
        if "\r\n\r\n" in data:
            startBody = True
            buffer = data.split("\r\n\r\n")[1]
            body_length += len(buffer)
        while content_length != body_length:
            recvData = socket.request.recv(1024)
            if "\r\n\r\n" in recvData and startBody == False:
                startBody = True
                buffer = recvData.decode().split("\r\n\r\n")[1]
                body_length += len(buffer)
            else:
                buffer += recvData.decode()
                body_length += len(recvData.decode())
        #body now contains all received data
        bodySections = buffer.split(boundary)
        if path == "/enternewuser":
            user = bodySections[1].split("\r\n\r\n")[1]
            pwd = bodySections[2].split("\r\n\r\n")[1]
            rePwd = bodySections[3].split("\r\n\r\n")[1]
            retData = (user,pwd,rePwd)
        #remember to do something about pwd and repwd not being the same, ask adam/rachael
        #store account locally (user, pwd)
            accsInfo = file.open("storedAccs.txt", "a")
            accsInfo.write(str(user) + "," + str(pwd))
        elif path == "/loginuser":
            user = bodySections[1].split("\r\n\r\n")[1]
            pwd = bodySections[2].split("\r\n\r\n")[1]
        #check if login is in locally stored file
            retData = (user,pwd)
        elif path == "/comment":
            projDeats = bodySections[1].split("\r\n\r\n")[1]
            projDesc = bodySections[2].split("\r\n\r\n")[1]
            retData = (projDeats, projDesc)

    elif path == "/image-upload":
        buffer = bytearray(b'')
        #of format image, caption
        image = bytearray(b'')
        caption = bytearray(b'')
        startBody = False
        if b'\r\n\r\n' in data:
            startBody = True
            buffer = data.split(b'\r\n\r\n')[1]
            body_length += len(buffer)
        while content_length != body_length:
            recvData = socket.request.recv(1024)
            if startBody == False:
                if b'\r\n\r\n' in recvData:
                    startBody = True
                    buffer = recvData[recvData.find(b'\r\n\r\n') + len(b'\r\n\r\n'):]
                    body_length += len(buffer)
            else:
                buffer += recvData
                body_length += len(recvData)
        bodySections = buffer.split(boundary.encode())
        image = bodySections[1].split(b'\r\n\r\n')[1]
        caption = bodySections[2].split(b'\r\n\r\n')[1]
        retData = (image, caption)
        
        storeInfo = bytearray()
        storeInfo += image
        separator = ", "
        separator = separator.encode()
        storeInfo += separator
        storeInfo += caption
        #write storeinfo (image as bytes, caption as bytes) to file
        #storedProjects = file.open("storedProjects", "wb")
        #storedProjects.write()
    return retData