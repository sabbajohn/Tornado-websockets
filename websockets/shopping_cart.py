import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop
import tornado.options

from uuid import uuid4
from threading import Lock

class ShoppingCart(object):
	totalInventory = 10
	
	def __init__(self):
		self.callbacks = set()
		self.carts = set()
		self.lock = Lock()
	
	def register(self, callback):
		with self.lock:
			self.callbacks.add(callback)
	
	def unregister(self, callback):
		with self.lock:
			self.callbacks.remove(callback)
	
	def moveItemToCart(self, session):
		with self.lock:
			if session in self.carts:
				return
			
			self.carts.add(session)
		
		self.notifyCallbacks()
			
	def removeItemFromCart(self, session):
		with self.lock:
			if session not in self.carts:
				return
		
			self.carts.remove(session)
		
		self.notifyCallbacks()
	
	def notifyCallbacks(self):
		inventoryCount = self.getInventoryCount()
		
		with self.lock:
			for callback in self.callbacks:
				callback(inventoryCount)
	
	def getInventoryCount(self):
		with self.lock:
			return self.totalInventory - len(self.carts)

class DetailHandler(tornado.web.RequestHandler):
	def get(self):
		session = uuid4()
		count = self.application.shoppingCart.getInventoryCount()
		self.render("index.html", session=session, count=count)

class CartHandler(tornado.web.RequestHandler):
	def post(self):
		action = self.get_argument('action')
		session = self.get_argument('session')

		if not session:
			self.set_status(400)
			return

		if action == 'add':
			self.application.shoppingCart.moveItemToCart(session)
		elif action == 'remove':
			self.application.shoppingCart.removeItemFromCart(session)
		else:
			self.set_status(400)

class StatusHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		self.application.shoppingCart.register(self.callback)

	def on_close(self):
		self.application.shoppingCart.unregister(self.callback)

	def on_message(self, message):
		pass
	
	def callback(self, count):
		self.write_message('{"inventoryCount":"%d"}' % count)
		
class Application(tornado.web.Application):
	def __init__(self):
		self.shoppingCart = ShoppingCart()
		
		handlers = [
			(r'/', DetailHandler),
			(r'/cart', CartHandler),
			(r'/cart/status', StatusHandler)
		]
		
		settings = {
			'template_path': 'templates',
			'static_path': 'static'
		}
		
		super().__init__(handlers, **settings)

if __name__ == '__main__':
	tornado.options.parse_command_line()

	app = Application()
	server = tornado.httpserver.HTTPServer(app)
	server.listen(8000)
	tornado.ioloop.IOLoop.instance().start()
