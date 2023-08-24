import datetime
import json
import time
import urllib
import random
from tornado import httpclient, httpserver, ioloop, options, web, gen
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)


class IndexHandler(web.RequestHandler):
    @web.asynchronous
    @gen.coroutine
    def get(self):
        client = httpclient.AsyncHTTPClient()
        response = yield gen.Task(
            client.fetch,
            f"http://jsonplaceholder.typicode.com/photos/{random.randint(1, 5000)}",
        )
        body = json.loads(response.body)
        now = datetime.datetime.utcnow()
        self.write(
            """
                <div style="text-align: center">
                    <div style="font-size: 72px">%s</div>
                    <img src="%s" /></img>
                    <div style="font-size: 24px">repositories per second</div>
                </div>"""
            % (body["title"], body["url"])
        )
        self.finish()


if __name__ == "__main__":
    options.parse_command_line()
    app = web.Application(handlers=[(r"/", IndexHandler)])
    http_server = httpserver.HTTPServer(app)
    http_server.listen(options.port)
    ioloop.IOLoop.instance().start()
