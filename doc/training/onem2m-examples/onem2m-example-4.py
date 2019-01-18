# Example 4: Delete OneM2MRequest

from openmtc_onem2m.transport import OneM2MRequest

request = OneM2MRequest("delete", to="onem2m")

print(request.to)
#>>> onem2m
