from WebSQController import WebSQController
import os

#websq_domain = os.environ.get("WEBSQ_DOMAIN", 'http://localhost:8080/')
websq_domain = os.environ.get("WEBSQ_DOMAIN", 'http://localhost:8000/')
print(websq_domain)

sq = WebSQController(websq_domain)
#sq = WebSQController('http://localhost:8080/')

sq.getSettings()

