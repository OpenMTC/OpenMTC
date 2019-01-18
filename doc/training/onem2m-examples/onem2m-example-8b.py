# Example 8b: Making Requests

from openmtc_onem2m.client.http import OneM2MHTTPClient
from openmtc_onem2m.transport import OneM2MRequest

# create a OneM2MHTTPClient object
client = OneM2MHTTPClient("http://localhost:8000", False)

# create a OneM2MRequest object
onem2m_request = OneM2MRequest("retrieve", to="onem2m")
# send the OneM2MRequest to the CSE
promise = client.send_onem2m_request(onem2m_request)
# reteive the OneM2MResponse from the returned promise
onem2m_response = promise.get()

print(onem2m_response.to)
#>>> onem2m
print(onem2m_response.response_status_code)
#>>> STATUS(numeric_code=2000, description='OK', http_status_code=200)
print(onem2m_response.content)
#>>> CSEBase(path='None', id='cb0')
