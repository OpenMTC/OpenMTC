# Example 14a: Invoking a FlaskRunner

from openmtc_app.onem2m import XAE
from openmtc_app.flask_runner import FlaskRunner

class MyAE(XAE):
    def _on_register(self):
        pass

app_instance = MyAE()
runner = FlaskRunner(app_instance)
runner.run("http://localhost:8000")
