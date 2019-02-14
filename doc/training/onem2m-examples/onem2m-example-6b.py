# Example 6b: Notify OneM2MRequest with data

from openmtc_onem2m.transport import OneM2MRequest
import json

sensor_data = {"type": "temperature",
               "value": 15 }

data_string = json.dumps(sensor_data)

request = OneM2MRequest("create", 
                        to="onem2m",
                        pc=data_string,
                        ty="application/json")

print(request.to)
#>>> onem2m
print(request.pc)
#>>> {"type": "temperature", "value": 15}
