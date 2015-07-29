import os
import sys

import ifc_query

from ifc_query import formatters

fn = os.path.normpath(sys.argv[1])
assert os.path.isfile(fn)
file = ifc_query.open(fn)

output = ifc_query.xml_formatter()

output.ifcm.header.name                                     = file.header.file_name.name
output.ifcm.header.creationDate                             = file.header.file_name.time_stamp
output.ifcm.header.author                                   = file.header.file_name.author
output.ifcm.header.organization                             = file.header.file_name.organization
output.ifcm.header.preprocessor                             = file.header.file_name.preprocessor_version
output.ifcm.header.originatingSystem                        = file.header.file_name.originating_system
output.ifcm.header.authorization                            = file.header.file_name.authorization
output.ifcm.header.fileSchema                               = file.header.file_schema.schema_identifiers
output.ifcm.header.viewDefinition                           = file.header.file_description.description >> formatters.regex(r"ViewDefinition\s\[([^\]+])\]") >> formatters.split(",")
output.ifcm.header.exportOptions                            = file.header.file_description.description >> formatters.regex(r"ViewDefinition\s\[([^\]+])\]") >> formatters.split(",")
                                                            
output.ifcm.ifcparameters.ifcApplication                    = file.IfcApplication.ApplicationFullName
output.ifcm.ifcparameters.IfcGeometricRepresentationContext = file.IfcGeometricRepresentationContext.ContextType
output.ifcm.ifcparameters.ifcSiUnit                         = file.IfcSIUnit.Prefix + file.IfcSIUnit.Name
                                                            
output.ifcm.quantities.floorCount                           = file.IfcBuilding.IsDecomposedBy.RelatedObjects >> formatters.count
output.ifcm.quantities.roomCount                            = file.IfcSpace >> formatters.count
output.ifcm.quantities.wallCount                            = file.IfcWall >> formatters.count
output.ifcm.quantities.windowsCount                         = file.IfcWindow >> formatters.count
output.ifcm.quantities.doorCount                            = file.IfcDoor >> formatters.count
output.ifcm.quantities.pipeCount                            = file.IfcFlowSegment >> formatters.count
output.ifcm.quantities.columnCount                          = file.IfcColumn >> formatters.count
output.ifcm.quantities.numberOfComponents                   = file.IfcProduct >> formatters.count
output.ifcm.quantities.numberOfRelations                    = file.IfcRelationship >> formatters.count
output.ifcm.quantities.numberOfActors                       = file.IfcActor >> formatters.count
                                                            
output.ifcm.informationMetric.numberOfEntityTypesUsed       = file.measures.entityCount
output.ifcm.informationMetric.numberOfTotalEntitiesUsed     = file.measures.instanceCount
output.ifcm.informationMetric.optionalAttributes            = file.measures.optionalAttributesSet
                                                            
output.ifcm.Dependencies.webResourceLink                    = file.rdf_vocabularies

output.emit()