#Simple mapping of file extensions to html content types(as bytes)
mimetypes = {
    'txt'  : b'text/plain; charset=utf-8',
    'text' : b'text/plain',
    'html' : b'text/html',
    'js'   : b'text/javascript',
    'css'  : b'text/css',
    'png'  : b'image/png',
    'jpg'  : b'image/jpeg',
    'jpeg' : b'image/jpeg',
}

#Use the mimetypes dictionary to match file extensions to some known types, else return None
#If the extension doesnt exist as a key in our dictionary, then we likely never want to serve that file anyways(example:server.py)
def get_mimetype(filepath)->bytes:
    chunks = filepath.split('.')
    if chunks[-1] in mimetypes:
        return mimetypes[chunks[-1]]
    else:
        return None


def serve_htmltext_and_goto(self, token, text, link, time):
        if link != None:
            text += '<meta http-equiv="refresh" content="'+str(time)+'; url='+link+'" />'
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("X-Content-Type-Options", "nosniff")
        if token != None:
            self.send_header("Set-Cookie", "session-token=" + token + "; Max-Age=600")
        self.send_header("Content-Length", str(len(text)))
        self.end_headers()
        self.wfile.write(text.encode())


# used to turn cookies into a dictionary
def parse_cookies(cookie):
    cookies = {}
    cookie_list = cookie.split("; ")

    # keys and values are split on 
    for c in cookie_list:
        kv_pair = c.split("=")
        cookies.update({kv_pair[0]: kv_pair[1]})
    return cookies