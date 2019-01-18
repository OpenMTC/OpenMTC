# Example 11b: Updating a resource using OneM2MRequest Update

from openmtc_onem2m.model import AE
from openmtc_onem2m.client.http import OneM2MHTTPClient
from openmtc_onem2m.transport import OneM2MRequest

client = OneM2MHTTPClient("http://localhost:8000", False)

my_app = AE(App_ID="myApp", 
            labels=["keyword1", "keyword2"], 
            resourceName="MYAPP2", 
            requestReachability=False)

# Create the AE 'my_app' at the CSE
onem2m_request = OneM2MRequest("create", to="onem2m", ty=AE, pc=my_app)
promise = client.send_onem2m_request(onem2m_request)
onem2m_response = promise.get()
print(onem2m_response.content.labels)
#>>> [u'keyword1', u'keyword2']

# Retrieve the AE from the CSE and check the labels
path = "onem2m/" + onem2m_response.content.resourceName
onem2m_request = OneM2MRequest("retrieve", to=path)
promise = client.send_onem2m_request(onem2m_request)
onem2m_response = promise.get()
print(onem2m_response.content.labels)
#>>> [u'keyword1', u'keyword2']

# Update the changes labels in the remote resource
# Therefore a temporay AE object is needed
# This temporary AE object should ONLY contian the fields that need to be updated 
tmp_app = AE(labels=["foo", "bar", "coffee"])
onem2m_request = OneM2MRequest("update", to=path, pc=tmp_app)
promise = client.send_onem2m_request(onem2m_request)
onem2m_response = promise.get()
print(onem2m_response.content.labels)
#>>> [u'foo', u'bar', u'coffee']

# Set the local AE to the retrieved content
my_app = None
my_app = onem2m_response.content
print(my_app.labels)
#>>> [u'foo', u'bar', u'coffee']
