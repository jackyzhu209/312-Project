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