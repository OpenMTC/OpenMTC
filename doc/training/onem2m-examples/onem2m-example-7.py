# Example 7: Update OneM2MRequest

from openmtc_onem2m.transport import OneM2MRequest
from openmtc_onem2m.model import AE

my_app = AE(App_ID="myApp", labels=["keyword1", "keyword2"])

request = OneM2MRequest("update", to="onem2m", pc=my_app.labels)

print(request.to)
#>>> onem2m
print(request.pc)
#>>> [u'keyword1', u'keyword2']
