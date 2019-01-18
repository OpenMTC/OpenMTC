# Example 5a: Create OneM2MRequest

from openmtc_onem2m.transport import OneM2MRequest
from openmtc_onem2m.model import AE

my_app = AE(App_ID="myApp")

request = OneM2MRequest("create", to="onem2m", pc="my_app")

print(request.to)
#>>> onem2m
print(request.pc)
#>>> myApp
