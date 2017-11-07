# Example 18: Pushing Data

from openmtc_app.onem2m import XAE
from openmtc_app.flask_runner import FlaskRunner
from time import sleep
from somewhere import read_sensor_data

class MyAE(XAE):
    def _on_register(self):
        container = self.create_container(None, "myContainer")

	while True:
	    value = read_sensor_data() # read measurements
	    data = {"value": value}
	    self.push_content(container, data)
	    sleep(60)

app_instance = MyAE()
runner = FlaskRunner(app_instance)
runner.run("http://localhost:8000")
