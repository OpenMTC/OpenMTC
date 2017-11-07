from operator import attrgetter

def attrproperty(name):
	return property(attrgetter(name))

def resolve_attr(obj, attr):
	for name in attr.split("."):
		obj = getattr(obj, name)
	return obj