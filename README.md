IFC METADATA EXTRACTION
=======================

Abstract
--------
A semi-general purpose library is presented that simplifies mapping literal values
contained within an IFC file to RDF statements for archival purposes.


Installation
------------
This module depends on a binary python library for parsing IFC-SPF files called
[IfcOpenShell](https://github.com/aothms/IfcOpenShell). This repository comes with
platform-dependent libraries for Python 3.3 for Windows and Linux as well as a
version of [Portable Python](http://portablepython.com/wiki/PortablePython3.2.5.1/). 
For other platforms or Python versions users are required to build 
[IfcOpenShell](https://github.com/aothms/IfcOpenShell) themselves.


Examples
--------
Start with a Python REPL and invoke
    
    >>> import ifc_query
    >>> from ifc_query import formatters
    >>> file = ifc_query.open("Duplex_A_20110907_optimized.ifc")
    
    >>> file.IfcProject
    <Unbound query 'IfcProject'
      Entities:
      - #23515=IfcProject('1xS3BCk291UvhgP2a6eflL',#1,'0001',$,$,'Duplex Apartment','Project Status',(#3,#5137),#24098)
    >
    
The utility provides the file as the root node of a tree. One can descend into the
tree by an initial entity type node (IfcProject in this case). Subsequently,
attributes or inverse attributes of the entity instances, valid for that type, can
be used to descend further into the tree.

    >>> file.IfcProject.OwnerHistory
    <Unbound query 'IfcProject.OwnerHistory'
      Entities:
      - #1=IfcOwnerHistory(#18091,#8812,$,.NOCHANGE.,$,$,$,0)
    >

Lists of entity instance attributes are aggregated into the set of entities the
query instance operates on, for example:

    >>> file.IfcStair
    <Unbound query 'IfcStair'
      Entities:
      - #169=IfcStair('21ldoMpbP4VfsJ0XGY_34d',#1,'Stair:Residential - ...',#17844,$,'198878',.STRAIGHT_RUN_STAIR.),
      - #170=IfcStair('0wkEuT1wr1kOyafLY4v_O1',#1,'Stair:Residential - ...',#17718,$,'151086',.STRAIGHT_RUN_STAIR.)
    >
    
    >>> file.IfcStair.ObjectPlacement
    <Unbound query 'IfcStair.ObjectPlacement'
      Entities:
      - #17844=IfcLocalPlacement(#26,#4),
      - #17718=IfcLocalPlacement(#26,#4)
    >
    
When descending into attributes, which are not entity instances or lists of entity
instances, the query object becomes 'bound' and can be mapped to fields in the
output schema

    >>> file.IfcStair.Name
    <Bound query 'IfcStair.Name'
      Parameters:
      - IfcStair.Name: Stair:Residential - 200mm Max Riser 250mm Tread:198878,
      - IfcStair.Name: Stair:Residential - 200mm Max Riser 250mm Tread:151086
    >
    
    >>> file.IfcStair.Name >> "ifc:stair_name"
    <Bound query 'IfcStair.Name'
      Parameters:
      - ifc:stair_name: Stair:Residential - 200mm Max Riser 250mm Tread:198878,
      - ifc:stair_name: Stair:Residential - 200mm Max Riser 250mm Tread:151086
    >
    
When output by an rdf_formatter instance, this will emit something like:

    <project_7b7032ccb822417b9aea642906a29bd5> ifc:stair_name "Stair:Residential - 200mm Max Riser 250mm Tread:198878"^^xsd:string .
    <project_7b7032ccb822417b9aea642906a29bd5> ifc:stair_name "Stair:Residential - 200mm Max Riser 250mm Tread:151086"^^xsd:string .
    
Various formatters exist that are able to transform the parameters queries are bound
to in various ways, for example:

    >>> file.IfcPropertySingleValue.filter(Name="LoadBearing") >> formatters.count
    <Bound query 'IfcPropertySingleValue'
      Parameters:
      - IfcPropertySingleValue.Count: 2
    >

Geometric metadata
------------------

The following example lists the thickness for every wall in the model by aggregating the LayerThickness of its material layers.

    ifc_query.aggregate(file.IfcWallStandardCase).\
        HasAssociations.select("IfcRelAssociatesMaterial").RelatingMaterial.\
        select("IfcMaterialLayerSetUsage").ForLayerSet.MaterialLayers.LayerThickness \
            >> formatters.sum >> "duraark:IFCSPFFile/duraark:Wall/duraark:thickness"
            
The complete extracted output including geometric data is provided below
    
    @prefix duraark: <http://data.duraark.eu/vocab/buildm/> .
    @prefix geonames: <http://sws.geonames.org/> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix schema: <http://schema.org/> .
    @prefix unit: <http://qudt.org/vocab/unit#> .
    @prefix xsd112: <http://www.w3.org/TR/xmlschema11-2/#> .

    <http://data.duraark.eu/resource/ifcspffile_7b7032ccb822417b9aea642906a29bd5> a duraark:IFCSPFFile ;
         duraark:actorCount "0"^^xsd:nonNegativeInteger ;
         duraark:creator ""^^xsd:string ;
         duraark:creator "Author in header added by Thomas"^^xsd:string ;
         duraark:creator "This one as well"^^xsd:string ;
         duraark:creator "cskender "^^xsd:string ;
         duraark:dateCreated "2011-09-07T12:28:29"^^xsd:string ;
         duraark:entityCount "103"^^xsd:nonNegativeInteger ;
         duraark:filename "0001"^^xsd:string ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_27ece05cf06c4dd29ccd945e52597b0a> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_27ece05cf06c4dd29ccd945e52597fa3> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_2c39182207f84a2286a8a1e57412d365> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_2c39182207f84a2286a8a1e57412d386> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_2c39182207f84a2286a8a1e57412d8c1> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_2c39182207f84a2286a8a1e57412dcef> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_2c39182207f84a2286a8a1e57412df9e> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_2da40d624698436ca2c395c49bb70c3c> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_2da40d624698436ca2c395c49bb70ca4> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_2da40d624698436ca2c395c49bb70cfa> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_2da40d624698436ca2c395c49bb70d41> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_64b7f7d38cfc4277ba338de2e65338fa> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_64b7f7d38cfc4277ba338de2e6533a28> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_64b7f7d38cfc4277ba338de2e6533ae9> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_64b7f7d38cfc4277ba338de2e6533e77> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d4004> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d4065> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d40ce> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d4200> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d4257> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d4385> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d43b5> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d441c> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d44b8> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d46d1> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d46ec> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d471d> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d5239> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d5246> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d5275> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d5330> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d5393> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d548e> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d54e7> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d5512> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d55b5> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d5611> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d5659> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d568d> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d56c9> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d574f> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d7938> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d795d> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d7af9> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d7be7> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d7d12> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d7d42> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d7df1> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_e21226efc42d49079a6f46644e152770> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_e21226efc42d49079a6f46644e152771> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_e21226efc42d49079a6f46644e152773> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_e21226efc42d49079a6f46644e152776> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_e21226efc42d49079a6f46644e1527d2> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_e21226efc42d49079a6f46644e1527d3> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_e21226efc42d49079a6f46644e1527dc> ;
         duraark:hasObject <http://data.duraark.eu/resource/wall_e21226efc42d49079a6f46644e1527dd> ;
         duraark:hasType "Model"^^xsd:string ;
         duraark:hasType "Plan"^^xsd:string ;
         duraark:instanceCount "27530"^^xsd:nonNegativeInteger ;
         duraark:optionalAttributesSet "0.432674946654"^^xsd:double ;
         duraark:relationshipCount "2068"^^xsd:nonNegativeInteger ;
         duraark:unit unit:CubicMeter ;
         duraark:unit unit:Meter ;
         duraark:unit unit:SecondTime ;
         duraark:unit unit:SquareMeter .

    <http://data.duraark.eu/resource/physicalasset_7b7032ccb822417b9aea642906a29bd5> a duraark:PhysicalAsset ;
         duraark:buildingArea "123 (added by Thomas)"^^xsd:string ;
         duraark:buildingCount "1"^^xsd:nonNegativeInteger ;
         duraark:columnCount "0"^^xsd:nonNegativeInteger ;
         duraark:componentCount "295"^^xsd:nonNegativeInteger ;
         duraark:description "Project description added by Thomas"^^schema:Text ;
         duraark:doorCount "14"^^xsd:nonNegativeInteger ;
         duraark:floorCount "4"^^xsd:nonNegativeInteger ;
         duraark:identifier "1xS3BCk291UvhgP2a6eflL"^^xsd:string ;
         duraark:latitude "41.8744"^^xsd112:double ;
         duraark:location "http://sws.geonames.org/4890276"^^<http://www.w3.org/2003/01/geo/wgs84_pos#SpatialThing> ;
         duraark:longitude "-87.6393999997"^^xsd112:double ;
         duraark:name "Duplex Apartment"^^schema:Text ;
         duraark:spaceCount "21"^^xsd:nonNegativeInteger ;
         duraark:streetAddress "Enter address here"^^xsd:string ;
         duraark:wallCount "57"^^xsd:nonNegativeInteger ;
         duraark:windowCount "24"^^xsd:nonNegativeInteger .

    <http://data.duraark.eu/resource/wall_27ece05cf06c4dd29ccd945e52597b0a> a duraark:Wall ;
         duraark:thickness "0.152"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_27ece05cf06c4dd29ccd945e52597fa3> a duraark:Wall ;
         duraark:thickness "0.152"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_2c39182207f84a2286a8a1e57412d365> a duraark:Wall ;
         duraark:thickness "0.152"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_2c39182207f84a2286a8a1e57412d386> a duraark:Wall ;
         duraark:thickness "0.152"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_2c39182207f84a2286a8a1e57412d8c1> a duraark:Wall ;
         duraark:thickness "0.152"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_2c39182207f84a2286a8a1e57412dcef> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_2c39182207f84a2286a8a1e57412df9e> a duraark:Wall ;
         duraark:thickness "0.152"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_2da40d624698436ca2c395c49bb70c3c> a duraark:Wall ;
         duraark:thickness "0.417"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_2da40d624698436ca2c395c49bb70ca4> a duraark:Wall ;
         duraark:thickness "0.417"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_2da40d624698436ca2c395c49bb70cfa> a duraark:Wall ;
         duraark:thickness "0.417"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_2da40d624698436ca2c395c49bb70d41> a duraark:Wall ;
         duraark:thickness "0.417"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_64b7f7d38cfc4277ba338de2e65338fa> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_64b7f7d38cfc4277ba338de2e6533a28> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_64b7f7d38cfc4277ba338de2e6533ae9> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_64b7f7d38cfc4277ba338de2e6533e77> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d4004> a duraark:Wall ;
         duraark:thickness "0.435"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d4065> a duraark:Wall ;
         duraark:thickness "0.435"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d40ce> a duraark:Wall ;
         duraark:thickness "0.435"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d4200> a duraark:Wall ;
         duraark:thickness "0.417"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d4257> a duraark:Wall ;
         duraark:thickness "0.417"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d4385> a duraark:Wall ;
         duraark:thickness "0.417"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d43b5> a duraark:Wall ;
         duraark:thickness "0.417"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d441c> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d44b8> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d46d1> a duraark:Wall ;
         duraark:thickness "0.55"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d46ec> a duraark:Wall ;
         duraark:thickness "0.55"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d471d> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d5239> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d5246> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d5275> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d5330> a duraark:Wall ;
         duraark:thickness "0.184"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d5393> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d548e> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d54e7> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d5512> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d55b5> a duraark:Wall ;
         duraark:thickness "0.184"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d5611> a duraark:Wall ;
         duraark:thickness "0.417"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d5659> a duraark:Wall ;
         duraark:thickness "0.417"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d568d> a duraark:Wall ;
         duraark:thickness "0.417"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d56c9> a duraark:Wall ;
         duraark:thickness "0.417"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d574f> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d7938> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d795d> a duraark:Wall ;
         duraark:thickness "0.55"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d7af9> a duraark:Wall ;
         duraark:thickness "0.417"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d7be7> a duraark:Wall ;
         duraark:thickness "0.124"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d7d12> a duraark:Wall ;
         duraark:thickness "0.417"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d7d42> a duraark:Wall ;
         duraark:thickness "0.417"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_9808fd7fdc48478e9217628e833d7df1> a duraark:Wall ;
         duraark:thickness "0.417"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_e21226efc42d49079a6f46644e152770> a duraark:Wall ;
         duraark:thickness "0.054"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_e21226efc42d49079a6f46644e152771> a duraark:Wall ;
         duraark:thickness "0.054"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_e21226efc42d49079a6f46644e152773> a duraark:Wall ;
         duraark:thickness "0.054"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_e21226efc42d49079a6f46644e152776> a duraark:Wall ;
         duraark:thickness "0.054"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_e21226efc42d49079a6f46644e1527d2> a duraark:Wall ;
         duraark:thickness "0.054"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_e21226efc42d49079a6f46644e1527d3> a duraark:Wall ;
         duraark:thickness "0.054"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_e21226efc42d49079a6f46644e1527dc> a duraark:Wall ;
         duraark:thickness "0.054"^^xsd:decimal .

    <http://data.duraark.eu/resource/wall_e21226efc42d49079a6f46644e1527dd> a duraark:Wall ;
         duraark:thickness "0.054"^^xsd:decimal .
