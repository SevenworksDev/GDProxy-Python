import time, json, socketserver, http.server
from urllib import request, parse
from http import client

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

gdServer_url = config.get('gdServer', {}).get('url', "http://www.boomlings.com")
commentBan_enabled = config.get('commentBan', {}).get('enabled', False)
commentBan_banTime = config.get('commentBan', {}).get('banTime', 3600)
commentBan_banReason = config.get('commentBan', {}).get('banReason', "")
noLogin_enabled = config.get('noLogin', {}).get('enabled', False)
noLogin_noLoginCode = config.get('noLogin', {}).get('noLoginCode', -1)

ip_request_count = {}
ip_last_request_time = {}

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"GDProxy (Python Rewrite) by Sevenworks (https://github.com/SevenworksDev/GDProxy-Python) - Try sending a POST Request to this server the same you would send it to http://www.boomlings.com/database/something.php or use a GDPS Switcher tool like GDHM")
        else:
            self.send_error(404, "Not Found", "Either you tried to send a GET Request to RobTops servers or RobTops servers returned HTTP 404.")

    def do_POST(self):
        ip = self.client_address[0]

        if ip in ip_last_request_time:
            elapsed_time = time.time() - ip_last_request_time[ip]
            if elapsed_time < 1:
                if ip_request_count.get(ip, 0) >= 4:
                    self.send_error(429, "Too Many Requests", "Rate limit exceeded. Please try again later.")
                    return

        ip_request_count[ip] = ip_request_count.get(ip, 0) + 1
        ip_last_request_time[ip] = time.time()

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        headers = {'User-Agent': ''}
        try:
            if commentBan_enabled and '/uploadGJComment21.php' in self.path:
                temp_response = f"temp_{commentBan_banTime}_{commentBan_banReason}" if commentBan_banTime and commentBan_banReason else -10
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(str(temp_response).encode('utf-8'))
                return

            if noLogin_enabled and '/accounts/loginGJAccount.php' in self.path:
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(str(noLogin_noLoginCode).encode('utf-8'))
                return

            req = request.Request(
                gdServer_url + self.path,
                data=post_data,
                headers=headers,
                method='POST'
            )

            with request.urlopen(req) as response:
                status_code = response.getcode()
                response_data = response.read().decode('utf-8')
                self.send_response(status_code)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(response_data.encode('utf-8'))

        except client.HTTPException as e:
            self.send_error(500, "Server Error", "GDProxy error has occurred, check the console if you are the developer.")
            print(f"str(e)")

with socketserver.TCPServer(("", 30700), RequestHandler) as httpd:
    print(f"GDProxy is now being served on 127.0.0.1:30700")
    httpd.serve_forever()
