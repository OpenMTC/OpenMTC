# Example 15: Running App with Static Information

from openmtc_app.onem2m import XAE

class MyAE(XAE):
    app_id = "AnotherAppID"
    labels =["keyword1", "keyword2"]
