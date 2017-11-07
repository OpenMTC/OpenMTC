# Example 13: Minimal application

from openmtc_app.onem2m import XAE

class MyAE(XAE):
    # when this is called the application is registered 
    # and can start doing something
    def _on_register(self):
        pass
