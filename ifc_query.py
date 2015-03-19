import re
import sys
import json
import string
import datetime
import ifcopenshell
from collections import namedtuple
import operator

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
                return sum(li, query.instance_list())
            return li
        def __repr__(self):
            return ",\n".join("  - %s"%v.instance for v in self.instances)
        def __len__(self): return len(self.instances)
        def select(self, ty):
            return query.instance_list(
                self.prefix, 
                [i for i in self.instances if i.instance.wrapped_data.is_a(ty)]
            )
            
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
        def __init__(self, li=None):
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
        def unique(self):
            value_set = set()
            result = query.parameter_list()
            for k, v in self.li:
                if v not in value_set:
                    value_set.add(v)
                    result.li.append((k, v))
            return result
        def apply(self, fn):
            return query.parameter_list([(k, fn(v)) for k, v in self.li])
        def filter(self, regex):
            return query.parameter_list([(k, regex.evaluate(v)) for k, v in self.li if regex.matches(v)])
        def __repr__(self):
            return ",\n".join("  - %s: %s"%(k,v) for k,v in self.li)

    
    def __init__(self, instances, prefix=None):
        self.prefix = prefix or ""
        if instances == [[]]: instances = []
        is_instance_list = isinstance(instances, query.instance_list)
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
        elif isinstance(other, query_count):
            # `other` is the formatters.count object, which means we add a new result parameter and initialize it to
            # the amount of instances
            q.params = query.parameter_list.count(self)
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
    def __init__(self, schema, ns, name_query, prefixes):
        self.schema_dom = parse_xml(schema)
        self.ns = ns
        self.uri = name_query.params.li[0][1]
        self.prefixes = list(prefixes.items())
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
            return uri
        
        def typify(pred, s):
            schema_type = lookup(pred)
            if hasattr(s, 'to_rdf'): return typify(pred, s.to_rdf())
            elif schema_type is not None: return '"%s"^^%s'%(escape(str(s)), schema_type)
            elif isinstance(s, int): return '"%d"^^xsd:integer'%s
            elif isinstance(s, float): return '"%r"^^xsd:decimal'%s            
            elif self.matches_prefix(s): p,n = self.matches_prefix(s); return s.replace(n,p+':')
            else: return '"%s"^^xsd:string'%escape(str(s))
        
        def walk():
            for item in li:
                for p in item.params.li:
                    if p[1] is not None:
                        predicates = p[0] if isinstance(p[0], (tuple, list)) else [p[0]]
                        for pred in predicates:
                            yield pred, typify(pred, p[1])
                            
        def make_instance(pred):
            cls, prop = pred.split('/')
            return "<%s%s_%s>" % (self.ns, cls.lower().split(':')[1], self.uri), cls, prop

        for ns in self.prefixes:
            print("@prefix %s: %s ."%ns)
        
        print("")
        
        def emit():
            instances = set()
            for pred, value in walk():
                uri, cls, prop = make_instance(pred)
                if uri not in instances:
                    instances.add(uri)
                    yield (uri, "a", cls)
                yield (uri, prop, value)
                
        statements = sorted(emit())
        ps = None
        for s,p,o in statements:
            if ps is not None:
                sys.stdout.write(" ;\n" if ps == s else " .\n\n")
            sys.stdout.write(" ".join(("    " if ps == s else s,p,o)))
            ps = s
        sys.stdout.write(" .\n")
        