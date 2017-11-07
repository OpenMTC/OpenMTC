"""
Dependencies:
    pip install tabulate bson simplejson python-cjson ujson demjson yajl msgpack-python jsonpickle jsonlib jsonlib2 dill
"""
 
from timeit import timeit 
from tabulate import tabulate
 
setup = '''d = {
    'words': """
        Lorem ipsum dolor sit amet, consectetur adipiscing 
        elit. Mauris adipiscing adipiscing placerat. 
        Vestibulum augue augue, 
        pellentesque quis sollicitudin id, adipiscing.
        """,
    'list': range(100),
    'dict': dict((str(i),'a') for i in xrange(100)),
    'int': 100,
    'float': 100.123456
}'''
 
setup_cpickle    = '%s ; src = cPickle.dumps(d)' % setup
setup_cpickle_binary   = '%s ; src = cPickle.dumps(d, 2)' % setup
setup_json      = '%s ; import json; src = json.dumps(d)' % setup
setup_bson      = '%s ; src = dumps(d)' % setup
setup_msgpack   = '%s ; src = msgpack.dumps(d)' % setup
setup_json_pickle   = '%s ; src = jsonpickle.encode(d)' % setup
setup_b64_pickle   = '%s ; src = base64.b64encode(cPickle.dumps(d, 2))' % setup
setup_b64_dill   = '%s ; src = base64.b64encode(dill.dumps(d, 2))' % setup
 
tests = [
    # (title, setup, enc_test, dec_test)
    ('pickle (ascii)', 'import pickle; import cPickle; %s' % setup_cpickle, 'pickle.dumps(d, 0)', 'pickle.loads(src)'),
    ('pickle (binary)', 'import pickle; import cPickle; %s' % setup_cpickle_binary, 'pickle.dumps(d, 2)', 'pickle.loads(src)'),
    ('cPickle (ascii)', 'import cPickle; %s' % setup_cpickle, 'cPickle.dumps(d, 0)', 'cPickle.loads(src)'),
    ('cPickle (binary)', 'import cPickle; %s' % setup_cpickle_binary, 'cPickle.dumps(d, 2)', 'cPickle.loads(src)'),
    ('json', 'import json; %s' % setup_json, 'json.dumps(d)', 'json.loads(src)'),
    ('json-check_circular', 'import json; %s' % setup_json, 'json.dumps(d, check_circular=False)', 'json.loads(src)'),
    ('json+indent', 'import json; %s' % setup_json, 'json.dumps(d, indent=2)', 'json.loads(src)'),
    ('bson 0.3.3', 'from bson import dumps, loads; %s' % setup_bson, 'dumps(d)', 'loads(src)'),
    # if there are problems with bson. Change the line on top with this one 
    # ('bson 0.3.3', 'from bson.json_util import dumps, loads; %s' % setup_bson, 'dumps(d)', 'loads(src)'),
    ('simplejson-3.3.1', 'import simplejson; %s' % setup_json, 'simplejson.dumps(d)', 'simplejson.loads(src)'),
    ('python-cjson-1.1.0', 'import cjson; %s' % setup_json, 'cjson.encode(d)', 'cjson.decode(src)'),
    ('ujson-1.33', 'import ujson; %s' % setup_json, 'ujson.dumps(d)', 'ujson.loads(src)'),
    # ('demjson 2.2.2', 'import demjson; %s' % setup_json, 'demjson.encode(d)', 'demjson.decode(src)'),
    ('yajl 0.3.5', 'import yajl; %s' % setup_json, 'yajl.dumps(d)', 'yajl.loads(src)'),
    ('msgpack-python-0.3.0', 'import msgpack; %s' % setup_msgpack, 'msgpack.dumps(d)', 'msgpack.loads(src)'),
    ('jsonpickle 0.9.1', 'import jsonpickle; %s' % setup_json_pickle, 'jsonpickle.encode(d)', 'jsonpickle.decode(src)'),
    ('jsonlib 1.6.1', 'import jsonlib; %s' % setup_json, 'jsonlib.write(d)', 'jsonlib.read(src)'),
    ('jsonlib2 1.5.2', 'import jsonlib2; %s' % setup_json, 'jsonlib2.write(d)', 'jsonlib2.read(src)'),
    ('b64Pickle', 'import cPickle; import base64; %s' % setup_b64_pickle, 'base64.b64encode(cPickle.dumps(d, 2))', 'cPickle.loads(base64.b64decode(src))'),
    ('b64Dill', 'import dill; import base64; %s' % setup_b64_dill, 'base64.b64encode(dill.dumps(d, 2))', 'dill.loads(base64.b64decode(src))'),
]
 
loops = 1000
enc_table = []
dec_table = []
 
print "Running tests (%d loops each)" % loops
 
for title, mod, enc, dec in tests:
    print title
 
    print "  [Encode]", enc 
    result = timeit(enc, mod, number=loops)
    enc_table.append([title, result])
 
    print "  [Decode]", dec 
    result = timeit(dec, mod, number=loops)
    dec_table.append([title, result])
 
enc_table.sort(key=lambda x: x[1])
enc_table.insert(0, ['Package', 'Seconds'])
 
dec_table.sort(key=lambda x: x[1])
dec_table.insert(0, ['Package', 'Seconds'])
 
print "\nEncoding Test (%d loops)" % loops
print tabulate(enc_table, headers="firstrow")
 
print "\nDecoding Test (%d loops)" % loops
print tabulate(dec_table, headers="firstrow")
