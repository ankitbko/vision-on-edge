from tornado import web, ioloop
import frame_handler


class IndexHandler(web.RequestHandler):
    """Handler for the root endpoint for the application running on
    Tornado Web Server. Not used to handle requests

    Args:
        web (_type_): Request handler
    """

    def get(self):
        self.render('index.html')


app = web.Application([
    (r'/', IndexHandler),
    (r'/ws/frame', frame_handler.FrameHandler),
    (r'/ws/frame_internal', frame_handler.FrameHandlerInternal),
])


def start_server():
    app.listen(7001)
    print("Starting server")
    ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    start_server()
