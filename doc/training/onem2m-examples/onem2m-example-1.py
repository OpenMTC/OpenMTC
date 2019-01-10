# Example 1: Creating Objects

from openmtc_onem2m.model import AE

my_app = AE()

print(my_app.path)
#>>> None
print(my_app.App_ID)
#>>> None
print(my_app.parent_path)
#>>> None
print(my_app.labels)
#>>> None
print(my_app.attributes)
#>>> [UnicodeAttribute(name="AE-ID", type=unicode), UnicodeAttribute(name="App-ID", type=unicode), ListAttribute(name="accessControlPolicyIDs", type=list), ListAttribute(name="announceTo", type=list), UnicodeAttribute(name="announcedAttribute", type=unicode), ListAttribute(name="childResources", type=list), DatetimeAttribute(name="creationTime", type=datetime), DatetimeAttribute(name="expirationTime", type=datetime), UnicodeAttribute(name="labels", type=unicode), DatetimeAttribute(name="lastModifiedTime", type=datetime), UnicodeAttribute(name="name", type=unicode), UnicodeAttribute(name="nodeLink", type=unicode), UnicodeAttribute(name="ontologyRef", type=unicode), ListAttribute(name="pointOfAccess", type=list)]
