import csv
import uuid
import os
import tornado.ioloop
import tornado.web

import tasks

__UPLOADS__ = 'uploads'

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        if self.get_cookie('user'):
            print "Welcome"+self.get_cookie('user')
        else:
            user_id = str(uuid.uuid4())
            self.set_cookie('user', user_id)
        self.render("index.html")

class Upload(tornado.web.RequestHandler):
    def post(self):
        fileinfo = self.request.files['filearg'][0]
        fname = fileinfo['filename']
        extn = os.path.splitext(fname)[1]
        cname = str(uuid.uuid4()) + extn
        fh = open(__UPLOADS__ + cname, 'w')
        tasks.scrape.delay(fileinfo['body'].split('\r\n')[1:100])
        fh.write(fileinfo['body'])

        self.finish(cname + " is uploaded!! Check %s folder" %__UPLOADS__)


if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r'/upload', Upload)
    ], Debug = True)
    application.listen(8890)
    tornado.ioloop.IOLoop.current().start()
