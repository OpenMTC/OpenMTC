# Example 12b: Forwarding

from openmtc_onem2m.client.http import OneM2MHTTPClient
from openmtc_onem2m.transport import OneM2MRequest

client = OneM2MHTTPClient("http://localhost:8000", False)

onem2m_request = OneM2MRequest("retrieve", to="onem2m")
onem2m_response = client.send_onem2m_request(onem2m_request).get()
print("---> Request to: http://localhost:8000" + "/" + onem2m_request.to)
print(onem2m_response.to)
#>>> onem2m
print(onem2m_response.response_status_code)
#>>> STATUS(numeric_code=2000, description='OK', http_status_code=200)
print(onem2m_response.content)
#>>> CSEBase(path='None', id='cb0')

onem2m_request = OneM2MRequest("retrieve", to="~/mn-cse-1/onem2m")
onem2m_response = client.send_onem2m_request(onem2m_request).get()
print("---> Request to: http://localhost:8000" + "/" + onem2m_request.to)
print(onem2m_response.to)
#>>> ~/mn-cse-1/onem2m
print(onem2m_response.response_status_code)
#>>> STATUS(numeric_code=2000, description='OK', http_status_code=200)
print(onem2m_response.content)
#>>> CSEBase(path='None', id='cb0')

client.port = 18000
onem2m_request = OneM2MRequest("retrieve", to="~/mn-cse-1/onem2m")
onem2m_response = client.send_onem2m_request(onem2m_request).get()
print("---> Request to: http://localhost:18000" + "/" + onem2m_request.to)
print(onem2m_response.to)
#>>> ~/mn-cse-1/onem2m
print(onem2m_response.response_status_code)
#>>> STATUS(numeric_code=2000, description='OK', http_status_code=200)
print(onem2m_response.content)
#>>> CSEBase(path='None', id='cb0')
