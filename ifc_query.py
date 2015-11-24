import re
import sys
import json
import string
import datetime
import itertools
import ifcopenshell
from collections import namedtuple, defaultdict
import operator
import inspect
import functools

from xml.dom.minidom import parse as parse_xml

try: from functools import reduce
except: pass

import rdf_extractor

class query(object):
    class instance_list(object):
        def __init__(self, prefix=None, instances=None):
            self.prefix = prefix or ''
            self.instances = instances or []
        def __add__(self, other):
            return query.instance_list(
                self.prefix if len(self.prefix) > len(other.prefix) else other.prefix,
                self.instances + other.instances
            )
        def __getattr__(self, k):
            li = list(map(lambda e: getattr(e, k), self.instances))
            classes = list(map(type, li))
            if query.instance_list in classes:
                return sum(filter(lambda v: isinstance(v, query.instance_list), li), query.instance_list())
            return li
        def __repr__(self):
            return ",\n".join("  - %s"%v.instance for v in self.instances)
        def __len__(self): return len(self.instances)
        def select(self, ty):
            return query.instance_list(
                self.prefix, 
                [i for i in self.instances if i.instance.wrapped_data.is_a(ty)]
            )
                
    class grouped_instance_list(object):
        def __init__(self, prefix=None, instances=None):
            self.prefix = prefix or ''
            self.instances = list(map(lambda x: query.instance_list(self.prefix, [x]), instances or []))
            self.names = list(map(ifcopenshell.guid.expand, map(lambda x: x.GlobalId[0], self.instances)))
        def __getattr__(self, k):
            il = query.grouped_instance_list(self.prefix)
            il.instances = list(map(lambda x: getattr(x, k), self.instances))
            il.names = self.names
            if set(map(type, il.instances)) == {list}:
                attr_type = set([type(b) for a in il.instances for b in a])
                if attr_type == {query.instance}:
                    il.instances = list(map(lambda x: query.instance_list(il.prefix, x), il.instances))
                else:
                    il.instances = list(map(lambda nm, x: query.parameter_list(list(map(lambda y: (il.prefix, y), x)), [nm]), il.names, il.instances))
            return il
        def select(self, ty):
            il = query.grouped_instance_list(self.prefix)
            il.instances = list(map(lambda x: x.select(ty), self.instances))
            il.names = self.names
            return il
        def __repr__(self):
            return "\n".join(map(lambda q: "[\n%s\n]" % repr(q), self.instances))
            
    class instance(object):
        def __init__(self, prefix, instance):
            self.prefix = prefix
            self.instance = instance
        def wrap_value(self, v, k):
            wrap = lambda e: query.instance("%s.%s"%(self.prefix,k), e)
            if isinstance(v, ifcopenshell.entity_instance): return wrap(v)
            elif isinstance(v, (tuple, list)) and len(v):
                classes = list(map(type, v))
                if ifcopenshell.entity_instance in classes: 
                    return query.instance_list("%s.%s"%(self.prefix,k), list(map(wrap, v)))
            return v
        def __getattr__(self, k):
            return self.wrap_value(getattr(self.instance, k), k)
            
    class parameter_list(object):
        def __init__(self, li=None, data=None):
            vector_names = ['int_vector', 'float_vector', 'double_vector', 'string_vector', 'material_vector']
            vector_types = set(getattr(ifcopenshell.ifcopenshell_wrapper, nm) for nm in vector_names)
            self.li = []
            def walk():
                for nm, val in (li or []):
                    if type(val) in vector_types:
                        for v in val:
                            self.li.append((nm, v))
                    else: self.li.append((nm, val))
            walk()
            self.data = data                
        def __add__(self, other):
            return query.parameter_list(self.li + other.li)
        def __or__(self, other):
            result = query.parameter_list()
            for i in range(max(len(self.li), len(other.li))):
                a1,b1, a2,b2 = '', None, '', None
                try: a1, b1 = self.li[i]
                except: pass
                try: a2, b2 = other.li[i]
                except: pass
                result.li.append((a1 if len(a1) > len(a2) else a2, b1 if b1 else b2))
            return result
        def __and__(self, other):
            e = lambda s: s if s else ""
            result = query.parameter_list()
            for i in range(max(len(self.li), len(other.li))):
                a1,b1, a2,b2 = '', None, '', None
                try: a1, b1 = self.li[i]
                except: pass
                try: a2, b2 = other.li[i]
                except: pass
                result.li.append(('(%s + %s)'%(a1, a2), e(b1) + e(b2)))
            return result
        def bind(self, name):
            return query.parameter_list([(name, v) for old_name, v in self.li])
        @staticmethod
        def count(query):
            return query.parameter_list([("%s.Count"%(query.prefix), len(query.entities))])
        def sum(self):
            return sum(map(operator.itemgetter(1), self.li))
        def unique(self):
            value_set = set()
            result = query.parameter_list()
            for k, v in self.li:
                if v not in value_set:
                    value_set.add(v)
                    result.li.append((k, v))
            return result
        def apply(self, fn):
            def flatten_functor(fn):
                while not (inspect.isfunction(fn) or inspect.ismethod(fn)):
                    if hasattr(fn, '__init__'): fn = fn.__init__
                    elif hasattr(fn, '__call__'): fn = fn.__call__
                    else: raise ValueError("%r of type %r is not callable" % (fn, type(fn)))
                return fn

            def get_arg_count(fn):
                """
                A wrapper that returns the length of arguments returned
                by inspect.getargspec() but ignores the 'self' argument
                on bound methods and handles functools.partial instances
                """
                if isinstance(fn, functools.partial):
                    fn2, applied = fn.func, len(fn.args)
                else:
                    fn2, applied = fn, 0
                return len(list(filter(lambda arg_name: arg_name != 'self', inspect.getargspec(flatten_functor(fn2)).args))) - applied
                
            argc = get_arg_count(fn)
            if argc > 1:
                simplify = lambda x: x.to_rdf() if hasattr(x, 'to_rdf') else x
                argv = map(simplify, map(operator.itemgetter(1), self.li))
                res = []
                if argc == len(argv):
                    k = ",".join(map(operator.itemgetter(0), self.li))
                    res = [(k, fn(*argv))]
                return query.parameter_list(res)
            else:
                return query.parameter_list([(k, fn(v)) for k, v in self.li])
                
        def filter(self, regex):
            return query.parameter_list([(k, regex.evaluate(v)) for k, v in self.li if regex.matches(v)])
        def __repr__(self):
            return ",\n".join("  - %s: %s"%(k,v) for k,v in self.li)

    
    def __init__(self, instances, prefix=None):
        self.prefix = prefix or ""
        if instances == [[]]: instances = []
        is_instance_list = isinstance(instances, (query.instance_list, query.grouped_instance_list))
        if not is_instance_list:
            classes = list(map(type, instances))
            if query.instance in classes or len(instances) == 0:
                is_instance_list = True
                instances = query.instance_list(self.prefix, instances)                
        if is_instance_list:
            self.entities = instances
            self.params = None
        else:
            self.entities = None
            self.params = query.parameter_list([(self.prefix, v) for v in instances])
    def select(self, ty):
        return query(self.entities.select(ty), self.prefix)
    def __getattr__(self, k):
        if self.params: 
            return query([], "%s.%s"%(self.prefix,k))
        return query(getattr(self.entities, k), "%s.%s"%(self.prefix,k))
    def __or__(self, other):
        if self.entities and other.entities:
            q = query(self.entities + other.entities, self.prefix)
        elif self.params and other.params:
            q = query([], self.prefix)
            q.params = self.params | other.params
        else: raise AttributeError()
        return q
    def __rshift__(self, other):
        q = query([], self.prefix)
        if isinstance(other, str) or (isinstance(other, (tuple, list)) and set(map(type,other)) == {str}): 
            # `other` is a string that describes the new name bound to the parameters in this query object
            q.params = (self.params or query.parameter_list()).bind(other)
            try: q.params.data = self.params.data
            except: pass
        elif isinstance(other, query_count):
            # `other` is the formatters.count object, which means we add a new result parameter and initialize it to
            # the amount of instances
            q.params = query.parameter_list.count(self)
        elif isinstance(other, query_sum):
            if isinstance(self.entities, query.grouped_instance_list):
                data = list(map(lambda li: li.data[0], self.entities.instances))
                q.params = query.parameter_list(list(map(lambda li: (self.prefix, li.sum()), self.entities.instances)), data)
            elif self.params:
                li = list(map(operator.itemgetter(1), self.params.li))
                if len(li):
                    q.params = query.parameter_list([(self.prefix + ".Sum", sum(li))])
            else:
                raise AttributeError()
        elif isinstance(other, query_avg):
            if self.params:
                li = list(map(operator.itemgetter(1), self.params.li))
                if len(li):
                    avg = sum(li) / float(len(li))
                    q.params = query.parameter_list([(self.prefix + ".Average", avg)])
        elif isinstance(other, query_unique):
            # `other` is the formatters.unique object, which means filter out non-unique parameters
            q.params = (self.params or query.parameter_list()).unique()
        elif hasattr(other, '__call__'):
            # some lambda function, probably also an attribute of the formatters collection class
            q.params = (self.params or query.parameter_list()).apply(other)
        elif isinstance(other, regex):
            q.params = (self.params or query.parameter_list()).filter(other)
        elif isinstance(other, split):
            orig = (self.params or query.parameter_list())
            def generate():
                for k,v in orig.li:
                    for s in v.split(split.chr):
                        yield k,s
            q.params = query.parameter_list(list(generate()))
        else: raise
        return q
    def __add__(self, other):
        if isinstance(other, self.__class__):
            q = query([], self.prefix)
            q.params = (self.params or query.parameter_list()) & (other.params or query.parameter_list())
            return q
        else:
            return self >> (lambda s: (s or '') + other)
    def __mul__(self, other):
        res = []
        unwrap = lambda a: list(map(lambda l: l[0][1], map(operator.attrgetter('li'), a.entities.instances)))
        a, b = map(unwrap, (self, other))
        if len(a) == len(b) and len(a) > 0:
            ab = filter(lambda vs: vs[0] is not None and vs[1] is not None, zip(a, b))
            if len(ab) > 0:
                a, b = zip(*ab)
                res = map(operator.mul, a, b)
        return query(res, "%s * %s" % (self.prefix, other.prefix))
    def __xor__(self, other):
        q = query([], self.prefix)
        q.params = (self.params or query.parameter_list()) + (other.params or query.parameter_list())
        return q
            
    def filter(self, **kwargs):
        pattern_class = re.compile("").__class__
        def matches(entity):
            for k, v in kwargs.items():
                val = getattr(entity, k)
                if isinstance(v, pattern_class):
                    if not val or v.match(val) is None: return False
                else:
                    if val != v: return False
            return True
        q = query([i for i in self.entities.instances if matches(i)], self.prefix)
        return q
        
    def __repr__(self):
        if self.entities:
            return "<Unbound query '%s'\n  Entities:\n%s\n>"%(self.prefix, self.entities)
        else:
            return "<Bound query '%s'\n  Parameters:\n%s\n>"%(self.prefix, self.params)
            
    def grouped(self):
        return query(query.grouped_instance_list(self.prefix, self.entities.instances), self.prefix)

            
class file(object):
    class file_measures(object):
        def __init__(self, file):
            entities = set()
            self._instanceCount = 0
            num_optional_attrs = 0
            num_optional_attrs_set = 0
            for inst in file:
                optional_attrs = list(i for i in range(len(inst)) if inst.wrapped_data.get_argument_optionality(i))
                optional_attrs_set = len(list(filter(lambda i: inst[i] is not None, optional_attrs)))
                
                num_optional_attrs += len(optional_attrs)
                num_optional_attrs_set += optional_attrs_set
                
                entities.add(inst.is_a())
                
                self._instanceCount += 1
            self._entityCount = len(entities)
            self._optionalAttributesSet = float(num_optional_attrs_set) / num_optional_attrs
            
            self._attrs = set(('instanceCount', 'entityCount', 'optionalAttributesSet'))
        def __getattr__(self, k):
            assert k in self._attrs
            return getattr(self, '_%s'%k)
            
    class query_wrapper(object):
        def __init__(self, *args):
            self.prefix, self.instance = args
        def __getattr__(self, k):
            return query.instance(self.prefix, getattr(self.instance, k))

    def __init__(self, ifcfile):
        self.file = ifcfile
        self.find_rdf_repos()
        self._measures = file.file_measures(ifcfile)
    def find_rdf_repos(self):
        def is_uri(s):
            if (s[0]+s[-1]) == '<>':
                if '#' in s: return s[1:-1].split('#')[0]
                else: return s[1:-1].rsplit('/', 1)[0]
            return None
        triples = rdf_extractor.obtain(self.file)
        vocabs = set()
        for spo in triples:
            for str in spo[1:]:
                uri = is_uri(str)
                if uri: vocabs.add(uri)
        self.rdf_vocabularies = query(sorted(vocabs), 'RdfVocabularies')
    def __getattr__(self, attr):
        if attr == 'header':
            return query([query.instance('<file header>', file.query_wrapper('<file header>', self.file.header))], '<file header>')
        elif attr == 'measures':
            return query([query.instance('<descriptive measures>', self._measures)], '<descriptive measures>')
        else:
            try: by_type = self.file.by_type(attr)
            except: raise AttributeError("file object does not have an attribute '%s'"%attr)
            instances = list(map(lambda e: query.instance(attr, e), by_type))
            return query(instances, attr)

def open(fn): return file(ifcopenshell.open(fn))

class query_unique(object): pass
class query_count(object): pass
class query_sum(object): pass
class query_avg(object): pass
class formatter(object): pass
class split(object):
    def __init__(self, chr): self.chr = chr
class regex(object):
    def __init__(self, pattern):
        self.rx = re.compile(pattern)
    def matches(self, value):
        return self.rx.search(value) is not None
    def evaluate(self, value):
        return self.rx.search(value).group(1)
    
class latlon(formatter):
    @staticmethod
    def to_float(compound):
        magnitudes = [1., 60., 3600., 3600.e6][:len(compound)]
        return sum(a/b for a,b in zip(compound, magnitudes))
    def __init__(self, *args):
        self.name, self.compound = args
    def __repr__(self):
        return "%s<%r>"%(self.name, self.compound)
    def to_rdf(self):
        return latlon.to_float(self.compound)

class xsd_date(str):
    def to_rdf(self): return '"%s"^^xsd:date'%self
        
formatters_list = [
    ("time"        , lambda ts: xsd_date(datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')) ),
    ("latitude"    , lambda v: None if v is None else latlon('Latitude', v)                                 ),
    ("longitude"   , lambda v: None if v is None else latlon('Longitude', v)                                ),
    ("join"        , lambda li: " ".join(li) if li else None                                                ),
    ("unique"      , query_unique()                                                                         ),
    ("count"       , query_count()                                                                          ),
    ("sum"         , query_sum()                                                                            ),
    ("avg"         , query_avg()                                                                            ),
    ("expand_guid" , ifcopenshell.guid.expand                                                               ),
    ("unit"        , lambda x: x                                                                            ),
    ("regex"       , regex                                                                                  ),
    ("split"       , split                                                                                  ),
    ("mapping"     , lambda cls: cls().__getitem__                                                          )
]
formatters = namedtuple("formatters_type", map(operator.itemgetter(0), formatters_list))(*map(operator.itemgetter(1),formatters_list))

class JsonFormatter(object):
    def __lshift__(self, li):
        di = {}
        for item in li:
            di.update(item.params)
        json.dump(di, sys.stdout, indent='  ')

json_formatter = JsonFormatter()

class rdf_formatter(object):
    def __init__(self, schema, ns, name_query, connection_predicates, prefixes):
        self.schema_dom = parse_xml(schema)
        self.ns = ns
        self.uri = name_query.params.li[0][1]
        self.prefixes = list(prefixes.items())
        self.connection_predicates = {(a,c): b for a,b,c in connection_predicates}
    def matches_prefix(self, uri):
        for prefix, namespace in self.prefixes:
            if uri.startswith(namespace[1:-1]): return (prefix, namespace[1:-1])
        return None
    def __lshift__(self, li):
        def escape(s):
            """
            Escape according to Turtle - Terse RDF Triple Language 3.3. String Escapes

            NB: Turtle can be UTF-8 encoded, but since output is written to stdout,
                which doesn't speak UTF-8 on Windows, all Unicode characters outside
                the printable character range of ASCII are escaped.
            """
            escape_dict = {
                '\t': '\\t',
                '\n': '\\n',
                '\r': '\\r',
                '"' : '\\"',
                '\\': '\\\\'
            }
            def escape_char(c):
                if c in escape_dict: return escape_dict.get(c)
                if ord(c) < 0x20 or ord(c) > 0x7e:
                    return "\\u%s"%"%04x"%ord(c)
                else: return c
            return ''.join(map(escape_char, s))
            
        def lookup(pred):
            if pred.count('/') == 2: return None
            
            cls, prop = map(lambda s: s.split(':')[1], pred.split('/'))
            def filterByDomainAndPredicate(node):
                if node.attributes['rdf:about'].value != prop: return False
                domains = node.getElementsByTagName('rdfs:domain')
                if len(domains) != 1: return False
                try:
                    val = domains[0].attributes['rdf:resource'].value
                    if val.startswith('#'): val = val[1:]
                    return val == cls
                except: return True
            props = list(filter(filterByDomainAndPredicate, self.schema_dom.getElementsByTagName('rdf:Property')))
            if len(props) != 1: return None
            ranges = props[0].getElementsByTagName('rdfs:range')
            if len(ranges) != 1: return None
            uri = ranges[0].attributes['rdf:resource'].value
            if self.matches_prefix(uri): 
                p,n = self.matches_prefix(uri); 
                uri = uri.replace(n,p+':')
            else:
                uri = "<%s>" % uri
            return uri
        
        def typify(pred, s):
            schema_type = lookup(pred)
            if hasattr(s, 'to_rdf'): return typify(pred, s.to_rdf())
            elif s is None: return None
            elif schema_type is not None: return '"%s"^^%s'%(escape(str(s)), schema_type)
            elif isinstance(s, int): return '"%d"^^xsd:integer'%s
            elif isinstance(s, float): return '"%s"^^xsd:decimal'%("%.7f"%s).rstrip('0')
            elif self.matches_prefix(s): p,n = self.matches_prefix(s); return s.replace(n,p+':')
            else: return '"%s"^^xsd:string'%escape(str(s))
        
        def walk():
            for item in li:
                for d, p in zip(item.params.data or [None] * len(item.params.li), item.params.li):
                    if p[1] is not None:
                        predicates = p[0] if isinstance(p[0], (tuple, list)) else [p[0]]
                        for pred in predicates:
                            val = typify(pred, p[1])
                            if val is not None:
                                yield d, pred, val
                            
        def make_instance(pred, element_id):
            if pred.count('/') == 1:
                cls, prop = pred.split('/')
                return "<%s%s_%s>" % (self.ns, cls.lower().split(':')[1], self.uri), None, cls, None, prop
            else:  
                cls1, cls2, prop = pred.split('/')
                a, b = "<%s%s_%s>" % (self.ns, cls1.lower().split(':')[1], self.uri), "<%s%s_%s>" % (self.ns, cls2.lower().split(':')[1], element_id)
                return a, b, cls1, cls2, prop                

        for ns in self.prefixes:
            print("@prefix %s: %s ."%ns)
        
        print("")
        
        def emit():
            instances = set()
            
            uris = defaultdict(list)
            
            for element_id, pred, value in walk():
                uri1, uri2, cls1, cls2, prop = make_instance(pred, element_id)
                
                for uri, cls in ((uri1, cls1), (uri2, cls2)):
                    if uri is None: continue
                    if uri not in instances:
                        instances.add(uri)
                        yield (uri, "a", cls)
                        uris[cls].append(uri)
                        
                if uri2 is None:
                    yield (uri1, prop, value)
                else:
                    yield (uri1, "duraark:hasObject", uri2)
                    yield (uri2, prop, value)
                    
            for a, b in itertools.permutations(uris.keys(), 2):
                pred = self.connection_predicates.get(tuple((a, b)))
                if pred is not None:
                    for c, d in itertools.product(uris[a], uris[b]):
                        yield (c, pred, d)                        
                
        statements = sorted(emit())
        ps = None
        for s,p,o in statements:
            if ps is not None:
                sys.stdout.write(" ;\n" if ps == s else " .\n\n")
            sys.stdout.write(" ".join(("    " if ps == s else s,p,o)))
            ps = s
        sys.stdout.write(" .\n")
        
class xml_formatter(object):
    class xml_formatter_attribute(object):
        def __init__(self, formatter, path):
            object.__setattr__(self, 'formatter', formatter)
            object.__setattr__(self, 'path', path)
        def __getattr__(self, k):
            return xml_formatter.xml_formatter_attribute(self.formatter, self.path + [k])
        def __setattr__(self, k, v):
            self.formatter.register(self.path + [k], v)
    def __init__(self):
        self.attributes = []
    def __getattr__(self, k):
        return xml_formatter.xml_formatter_attribute(self, [k])
    def register(self, path, vs):
        if vs.params is None: return
        for k, v in vs.params.li:
            if v is not None:
                self.attributes.append((path, v))
    def emit(self):
        import xml.etree.cElementTree as ET
        self.attributes.sort()
        previous_path = []
        nodes_by_path = {}
        root_path = None
        for path, value in self.attributes:
            for i, n in enumerate(path):
                node_path, parent_path = ".".join(path[0:i+1]), ".".join(path[0:i])
                if node_path in nodes_by_path and i < len(path) - 1: continue
                if root_path is None:
                    root_path = node_path
                    node = nodes_by_path[node_path] = ET.Element(n)
                else:
                    node = nodes_by_path[node_path] = ET.SubElement(nodes_by_path[parent_path], n)
            
            node.text = str(value)
        
        # tree = ET.ElementTree(nodes_by_path[root_path])
        sys.stdout.write(ET.tostring(nodes_by_path[root_path]))

aggregate = lambda q: q.grouped()
flatten = lambda q: q
