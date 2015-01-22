from __future__ import print_function

import rdflib

graph = rdflib.Graph()
graph.load("qudt-unit.ttl", format="turtle")
manager = rdflib.namespace.NamespaceManager(graph)


prefix = 'unit'
unit = dict(manager.namespaces())[prefix]
label_to_qname = dict()

for s,p,o in graph:
    if s.startswith(unit):
        if p == rdflib.namespace.RDFS.label:
            label_to_qname[o.lower()] = manager.qname(s)[len(prefix)+1:]
            
with open("qudt.py", "w") as file:
    print("unit_labels = {", file=file)
    for k, v in sorted(label_to_qname.items()):
        print("    %r: %r,"%tuple(map(str,(k,v))), file=file)
    print("}", file=file)
    print("", file=file)
    print("namespace = %r"%str(unit), file=file)
    print("", file=file)
    print("""class qudt:
def __getitem__(self, name):
    uri = name.lower().replace('_', ' ')
    if uri.endswith('metre'): uri = uri[:-5] + "meter"
    uri = unit_labels.get(uri, None)
    if uri: return namespace + uri
    else: return name
""")
