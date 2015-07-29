import os
import sys

import ifc_query

from ifc_query import formatters

fn = os.path.normpath(sys.argv[1])
assert os.path.isfile(fn)
file = ifc_query.open(fn)

output = ifc_query.xml_formatter()

output.ifcm.header.name                                     = file.header.file_name.name
# output.ifcm.header.creationDate                             =
# output.ifcm.header.author                                   =
# output.ifcm.header.organization                             =
# output.ifcm.header.preprocessor                             =
# output.ifcm.header.originatingSystem                        =
# output.ifcm.header.authorization                            =
# output.ifcm.header.fileSchema                               =
# output.ifcm.header.viewDefinition                           =
# output.ifcm.header.exportOptions                            =
                                                            
output.ifcm.ifcparameters.ifcApplication                    = file.IfcApplication.ApplicationFullName
# output.ifcm.ifcparameters.IfcGeometricRepresentationContext =
# output.ifcm.ifcparameters.ifcSiUnit                         =
                                                            
# output.ifcm.quantities.floorCount                           =
# output.ifcm.quantities.roomCount                            =
output.ifcm.quantities.wallCount                            = file.IfcWall >> formatters.count
# output.ifcm.quantities.windowsCount                         =
# output.ifcm.quantities.doorCount                            =
# output.ifcm.quantities.pipeCount                            =
# output.ifcm.quantities.columnCount                          =
# output.ifcm.quantities.numberOfComponents                   =
# output.ifcm.quantities.numberOfRelations                    =
# output.ifcm.quantities.numberOfActors                       =
                                                            
# output.ifcm.informationMetric.numberOfEntityTypesUsed       =
# output.ifcm.informationMetric.numberOfTotalEntitiesUsed     =
# output.ifcm.informationMetric.optionalAttributes            =
                                                            
# output.ifcm.Dependencies.webResourceLink                    =

output.emit()