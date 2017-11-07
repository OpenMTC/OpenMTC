# Example 16: Creating a simple Container

from openmtc_app.onem2m import XAE
from openmtc_app.flask_runner import FlaskRunner

class MyAE(XAE):
    def _on_register(self):
        container = self.create_container(None, "myContainer")

app_instance = MyAE()
runner = FlaskRunner(app_instance)
runner.run("http://localhost:8000")
