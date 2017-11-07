# Example 17: Creating a custom Container

from openmtc_app.onem2m import XAE
from openmtc_app.flask_runner import FlaskRunner
from openmtc_onem2m.model import Container

class MyAE(XAE):
    def _on_register(self):
		# create a container
        container = Container(
            resourceName = "myContainer",
            maxNrOfInstances=100,
            maxByteSize=1024 ** 3 )
        container = self.create_container(None, container)

app_instance = MyAE()
runner = FlaskRunner(app_instance)
runner.run("http://localhost:8000")
