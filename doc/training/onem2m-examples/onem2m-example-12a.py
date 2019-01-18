# Example 12a: Making Requests with error handling

from openmtc_onem2m.client.http import OneM2MHTTPClient
from openmtc_onem2m.transport import OneM2MRequest, OneM2MErrorResponse
from openmtc.exc import OpenMTCError

client = OneM2MHTTPClient("http://localhost:8000", False)

try:
    onem2m_request = OneM2MRequest("retrieve", to="onem2m")
    promise = client.send_onem2m_request(onem2m_request)
    onem2m_response = promise.get()
except OneM2MErrorResponse as e:
    print("CSE reported an error:", e)
    raise
except OpenMTCError as e:
    print("Failed to reach the CSE:", e)
    raise
else:
    pass

# no exception was raised, the method returned normally.
print(onem2m_response.to)
#>>> onem2m
print(onem2m_response.response_status_code)
#>>> STATUS(numeric_code=2000, description='OK', http_status_code=200)
print(onem2m_response.content)
#>>> CSEBase(path='None', id='cb0')
