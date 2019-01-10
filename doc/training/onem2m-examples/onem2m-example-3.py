# Example 3: Retrieve OneM2MRequest

from openmtc_onem2m.transport import OneM2MRequest

request = OneM2MRequest("retrieve", to="onem2m")

print(request.to)
#>>> onem2m
