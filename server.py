import csv
import json
import uuid
import os
import tornado.ioloop
import tornado.web
from tornado import web
import tornadoredis
import tasks
import redis
import datetime

redis_conn = redis.Redis('localhost', '6379')

settings = {
    'static_path': '/public',
    'redis': redis_conn,
    'Debug': True
}
public_root = os.path.join(os.path.dirname(__file__), 'public')
__UPLOADS__ = 'uploads'


class BaseHandler(tornado.web.RequestHandler):
    @property
    def redis(self):
        return self.settings['redis']


class FileStatusHandler(BaseHandler):
    def get(self, fname):
        self.write({
            'status': self.redis.get("status:%s" % fname)
        })


class FileGetHandler(tornado.web.RequestHandler):
    def get(self, filename):
        try:
            with open(filename, 'rb') as f:
                data = f.read()
                self.set_header('Content-Type', 'csv')
                self.set_header('Content-Disposition', 'attachment; filename=' + filename)
                self.write(data)
                self.finish()
        except:
            self.write("No file")


class MainHandler(BaseHandler):
    def get(self):
        if self.get_cookie('user'):
            print "Welcome" + self.get_cookie('user')
        else:
            user_id = str(uuid.uuid4())
            self.set_cookie('user', user_id)
        self.render("index.html")


class Upload(BaseHandler):
    def post(self):
        fileinfo = self.request.files['filearg'][0]
        fname = fileinfo['filename']
        extn = os.path.splitext(fname)[1]
        cname = str(uuid.uuid4())
        fh = open(__UPLOADS__ + cname + extn, 'w')
        tasks.scrape_async.delay(fileinfo['body'].split('\r\n')[1:], cname)
        fh.write(fileinfo['body'])
        user = self.get_cookie('user')
        redis_conn.lpush('users', user)
        redis_conn.lpush('users:%s:files' % user, fname)
        self.write({
            'fileId': cname,
            'fileName': fname,
            'user': user,
            'date': str(datetime.datetime.now()),
        })
        self.finish()


if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r'/upload', Upload),
        (r'/file/([^/]+)', FileGetHandler),
        (r'/status/([^/]+)', FileStatusHandler),
        (r'/public/(.*)', web.StaticFileHandler, {'path': public_root}), ], **{
        'static_path': 'public',
        'redis': redis_conn,
        'Debug': True
    })
    application.listen(8890)
    print "running at http://localhost:8890"
    tornado.ioloop.IOLoop.current().start()
