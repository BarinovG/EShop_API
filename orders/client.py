import requests
import logging
from pprint import pprint

# These two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

headers = {'Accept': '*/*',
           'Accept-Encoding': 'identity, deflate, compress, gzip',
           'Authorization': 'Token d1bb6c9f3599973bc9df794028a8a9613f7dddd3',
           'User-Agent': 'python-requests/0.12.1'}
url = 'http://127.0.0.1:8000/api/v1/products'
data = {
    "text": "pp"
}

resp_get = requests.get(url=url, headers=headers, data=data).json()



pprint(resp_get)
