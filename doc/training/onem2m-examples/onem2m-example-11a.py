# Example 11a: Create a resource (continued)

from openmtc_onem2m.model import AE
from openmtc_onem2m.client.http import OneM2MHTTPClient
from openmtc_onem2m.transport import OneM2MRequest

client = OneM2MHTTPClient("http://localhost:8000", False)

my_app = AE(App_ID="myApp", 
            labels=["keyword1", "keyword2"], 
            resourceName="MYAPP1", 
            requestReachability=False)

onem2m_request = OneM2MRequest("create", to="onem2m", ty=AE, pc=my_app)

promise = client.send_onem2m_request(onem2m_request)

onem2m_response = promise.get()

print(onem2m_response.response_status_code)
#>>> STATUS(numeric_code=2001, description='CREATED', http_status_code=201)

# Build path to retieve from
path = "onem2m/" + onem2m_response.content.resourceName
print(path)
#>>> onem2m/MYAPP

# Retrieve the AE from the CSE
onem2m_request = OneM2MRequest("retrieve", to=path)
promise = client.send_onem2m_request(onem2m_request)
onem2m_response = promise.get()

print(onem2m_response.response_status_code)
#>>> STATUS(numeric_code=2000, description='OK', http_status_code=200)
print(onem2m_response.content)
#>>> AE(path='None', id='ae0')

# Set the local AE to the retrieved content
my_app = None
my_app = onem2m_response.content

print(my_app.App_ID)
#>>> myApp
print(my_app.resourceName)
#>>> MYAPP
print(my_app.labels)
#>>> [u'keyword1', u'keyword2']
