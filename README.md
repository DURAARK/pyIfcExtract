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
