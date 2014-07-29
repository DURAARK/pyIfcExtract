import re
import sys

uri_pred = re.compile("^<(http://[^>]+)>$")
uri_val = re.compile("^(http://.+)$")
map = {'str':'string', 'int':'integer'}

def obtain(f):
    return_list = []
    es = f.by_type("IfcPropertySet")
    for e in es:
        os = e.PropertyDefinitionOf
        if len(os) == 1:
            ro = os[0].RelatedObjects
            for r in ro:
                guid = r.GlobalId
                props = e.HasProperties
                for prop in props:
                    if prop.wrapped_data.is_a("IfcPropertySingleValue"):
                        name = prop.Name
                        if name:
                            match = uri_pred.match(name)
                            predicate = object = None
                            predicate_is_uri = object_is_uri = False
                            if match:
                                name_uri = match.group(1)
                                predicate = '<%s>'%(name_uri)
                                predicate_is_uri = True
                            else:
                                predicate = '"%s"^^xsd:string'%(name)
                            val = prop.NominalValue
                            if val:
                                val = val.wrappedValue
                                if isinstance(val, str):
                                    match = uri_val.match(val)
                                    if match:
                                        val_uri = match.group(1)
                                        object = '<%s>'%(val_uri)
                                        object_is_uri = True
                                    else:
                                        ty = val.__class__.__name__
                                        object = '"%s"^^xsd:%s'%(str(val), map.get(ty, ty))
                            if predicate_is_uri:
                                return_list.append((":%s"%guid, predicate, object))
    return return_list