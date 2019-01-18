# Example 6a: Notify OneM2MRequest

from openmtc_onem2m.transport import OneM2MRequest
from openmtc_onem2m.model import AE

my_app = AE(App_ID="myApp")

request = OneM2MRequest("notify", to="onem2m", pc=my_app)

print(request.to)
#>>> onem2m
print(request.pc.App_ID)
#>>> myApp
