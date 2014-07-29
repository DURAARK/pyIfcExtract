import os
import sys
import ifc_query
from ifc_query import formatters

fn = os.path.normpath(sys.argv[1])
file = ifc_query.open(fn)

length_unit = file.IfcProject.UnitsInContext.Units.filter(UnitType="LENGTHUNIT")

ifc_query.rdf_formatter(
    file.IfcProject.GlobalId >> formatters.expand_guid,
    {   'xsd'        : '<http://www.w3.org/2001/XMLSchema#>'        ,
        'duraark'    : '<http://duraark.eu/voabularies/buildm#>'    ,
        'dc'         : '<http://purl.org/dc/elements/1.1/>'         ,
        'dct'        : '<http://purl.org/dc/terms/>'                ,
        'dbpedia-owl': '<http://dbpedia.org/ontology/>'             ,
        'dbp-prop'   : '<http://dbpedia.org/property/>'             ,
        'geo-pos'    : '<http://www.w3.org/2003/01/geo/wgs84_pos#>' ,
        'foaf'       : '<http://xmlns.com/foaf/0.1/>'               }
) << [
	
	file.IfcProject.GlobalId >> "duraark:object_identifier",

    (file.IfcProject.LongName | file.IfcProject.Name) >> "foaf:name",
    
    file.IfcProject.Description >> "dc:description",
    
    file.IfcProject.OwnerHistory.CreationDate >> formatters.time
        >> ("dbp-prop:startDate", "dbpedia-owl:buildingStartYear"),
    
    length_unit.select('IfcSIUnit').Prefix + length_unit.Name
        >> "duraark:length_unit",
        
    file.IfcApplication.ApplicationDeveloper.Name + ' ' +
        file.IfcApplication.ApplicationFullName + ' ' +
        file.IfcApplication.Version
        >> "duraark:authoring_tool",
        
    (file.IfcSite.RefLatitude >> formatters.latitude) +
        (file.IfcSite.RefLongitude >> formatters.longitude)
        >> "foaf:based_near",
        
    file.IfcBuilding.IsDecomposedBy.RelatedObjects >> formatters.count
        >> "duraark:floor_count",
        
    file.IfcSpace >> formatters.count >> "duraark:room_count",
    
    file.IfcBuilding.BuildingAddress.AddressLines >> formatters.join
        >> "dbpedia-owl:address",
        
    file.IfcOwnerHistory.OwningUser.ThePerson.GivenName + ' ' +
        file.IfcOwnerHistory.OwningUser.ThePerson.FamilyName
        >> formatters.unique >> "dc:creator",
        
    file.rdf_vocabularies >> "duraark:enrichment_vocabulary"
	
]
