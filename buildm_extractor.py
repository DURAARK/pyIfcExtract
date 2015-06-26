import os
import sys

import ifc_query

import util.geo
import util.qudt

from ifc_query import formatters

fn = os.path.normpath(sys.argv[1])
assert os.path.isfile(fn)
file = ifc_query.open(fn)

try: schema_file = sys.argv[2]
except: schema_file = 'buildm_v3.0.rdf'

geo_lookup = util.geo.lookup_factory(user_name="")

ifc_query.rdf_formatter(
    schema_file,
    'http://data.duraark.eu/resource/',
    file.IfcProject.GlobalId >> formatters.expand_guid,
    {   'xsd'        : '<http://www.w3.org/2001/XMLSchema#>'        ,
        'duraark'    : '<http://data.duraark.eu/vocab/>'            ,
        'schema'     : '<http://schema.org/>'                       ,
        'xsd112'     : '<http://www.w3.org/TR/xmlschema11-2/#>'     ,
        'unit'       : '<%s>'%util.qudt.namespace                   ,
        'geonames'   : '<http://sws.geonames.org/>'                 }
) << [
	file.header.file_name.author >> "duraark:IFCSPFFile/duraark:creator",

    file.header.file_name.organization >> "duraark:IFCSPFFile/duraark:creator",

    file.header.file_name.preprocessor_version >> "duraark:IFCSPFFile/duraark:authoringTool",

    file.header.file_name.originating_system >> "duraark:IFCSPFFile/duraark:authoringTool",

    file.header.file_schema.schema_identifiers >> "duraark:IFCSPFFile/duraark:fileSchema",

    file.header.file_description.description >> formatters.regex(r"ViewDefinition\s\[([^\]+])\]") >> formatters.split(",") >> "duraark:IFCSPFFile/duraark:viewDefinition",

    file.IfcOwnerHistory.OwningUser.ThePerson.GivenName + ' ' +
        file.IfcOwnerHistory.OwningUser.ThePerson.FamilyName
        >> formatters.unique >> "duraark:IFCSPFFile/duraark:creator",

    file.header.file_name.name >> "duraark:IFCSPFFile/duraark:name",

    file.header.file_name.time_stamp >> "duraark:IFCSPFFile/duraark:dateCreated",

	(file.IfcProject.LongName | file.IfcProject.Name) >> "duraark:PhysicalAsset/duraark:name",

    (file.IfcSite.RefLatitude >> formatters.latitude) >> "duraark:PhysicalAsset/duraark:latitude",

    (file.IfcSite.RefLongitude >> formatters.longitude) >> "duraark:PhysicalAsset/duraark:longitude",
    
    ((file.IfcSite.RefLatitude >> formatters.latitude)
        ^ (file.IfcSite.RefLongitude >> formatters.longitude))
        >> geo_lookup >> "duraark:PhysicalAsset/duraark:locatedIn",

    file.IfcBuilding.BuildingAddress.AddressLines >> formatters.join >> "duraark:PhysicalAsset/duraark:streetAddress",

    file.IfcProject.Description >> "duraark:PhysicalAsset/duraark:description",

    file.IfcProject.GlobalId >> "duraark:PhysicalAsset/duraark:identifier",

    file.IfcGeometricRepresentationContext.ContextType >> formatters.unique >> "duraark:IFCSPFFile/duraark:hasType",
    
    file.IfcGeometricRepresentationContext.Precision >> formatters.unique >> "duraark:IFCSPFFile/duraark:geometricPrecision",
    
    file.IfcGeometricRepresentationContext.CoordinateSpaceDimension >> formatters.unique >> "duraark:IFCSPFFile/duraark:dimensionCount",

    file.IfcProject.UnitsInContext.Units.select("IfcSIUnit").Prefix +
        file.IfcProject.UnitsInContext.Units.select("IfcSIUnit").Name >> formatters.mapping(util.qudt.qudt) >>
        "duraark:IFCSPFFile/duraark:unit",

    file.IfcBuilding.IsDefinedBy.RelatingPropertyDefinition.HasProperties.filter(Name="GrossPlannedArea").NominalValue.wrappedValue >> "duraark:PhysicalAsset/duraark:buildingArea",

    file.IfcBuilding >> formatters.count >> "duraark:PhysicalAsset/duraark:buildingCount",

    file.IfcBuilding.IsDecomposedBy.RelatedObjects >> formatters.count >> "duraark:PhysicalAsset/duraark:floorCount",

    file.IfcSpace >> formatters.count >> "duraark:PhysicalAsset/duraark:spaceCount",

    file.IfcWall >> formatters.count >> "duraark:PhysicalAsset/duraark:wallCount",

    file.IfcWindow >> formatters.count >> "duraark:PhysicalAsset/duraark:windowCount",

    file.IfcDoor >> formatters.count >> "duraark:PhysicalAsset/duraark:doorCount",

    file.IfcColumn >> formatters.count >> "duraark:PhysicalAsset/duraark:columnCount",

    file.IfcProduct >> formatters.count >> "duraark:PhysicalAsset/duraark:componentCount",

    file.IfcRelationship >> formatters.count >> "duraark:IFCSPFFile/duraark:relationshipCount",

    file.IfcActor >> formatters.count >> "duraark:IFCSPFFile/duraark:actorCount",

    file.IfcApplication.ApplicationFullName >> "duraark:IFCSPFFile/duraark:authoringTool",

    file.measures.optionalAttributesSet >> "duraark:IFCSPFFile/duraark:optionalAttributesSet",

    file.measures.instanceCount >> "duraark:IFCSPFFile/duraark:instanceCount",

    file.measures.entityCount >> "duraark:IFCSPFFile/duraark:entityCount",

    file.rdf_vocabularies >> "duraark:webResourceList"
]
