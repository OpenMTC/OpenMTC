# Example 10: Create a resource

from openmtc_onem2m.model import AE
from openmtc_onem2m.client.http import OneM2MHTTPClient
from openmtc_onem2m.transport import OneM2MRequest

# create a OneM2MHTTPClient object
client = OneM2MHTTPClient("http://localhost:8000", False)

# create a resource to be created on the CSE
# resourceName: (optional) for easy check in browser
# requestReachability: (mandatory) for servercapability of the AE
my_app = AE(App_ID="myApp", 
            labels=["keyword1", "keyword2"], 
            resourceName="MYAPP", 
            requestReachability=False)

# create a OneM2MRequest object of type 'create'
# ty: resource_type of the created resource
# pc: Resource content to be transferred
onem2m_request = OneM2MRequest("create", to="onem2m", ty=AE, pc=my_app)

# send the 'create' OneM2MRequest to the CSE
promise = client.send_onem2m_request(onem2m_request)

# reteive the OneM2MResponse from the returned promise
onem2m_response = promise.get()

print(onem2m_response.to)
#>>> onem2m
print(onem2m_response.response_status_code)
#>>> STATUS(numeric_code=2001, description='CREATED', http_status_code=201)
print(onem2m_response.content)
#>>> AE(path='None', id='ae0')
print(onem2m_response.content.App_ID)
#>>> myApp
print(onem2m_response.content.labels)
#>>> [u'keyword1', u'keyword2']
