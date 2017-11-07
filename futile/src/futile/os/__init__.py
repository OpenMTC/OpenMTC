

def get_fileobj(f):
    if not hasattr(f, "read"):
        return open(f)
    return f
