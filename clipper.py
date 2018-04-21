# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clipper
                                 A QGIS plugin
 This plugin lets you use clipping function in the same shapefile selecting
  a line or polygon clips all overlaying features
                              -------------------
        begin                : 2014-06-27
        latest                : 2018-04-20 
        copyright            : (C) 2014 by Giuseppe De Marco
        email                : demarco.giuseppe@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtXml
from qgis.core import *
from qgis.gui import *
# Initialize Qt resources from file resources.py
import resources_rc
#debug
import pdb
# Import the code for the dialog
#from clipperdialog import clipperDialog
import os.path


class clipper:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        localePath = os.path.join(self.plugin_dir, 'i18n', 'clipper_{}.qm'.format(locale))

        if os.path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        #self.dlg = clipperDialog()

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(
            QIcon(":/plugins/clipper/icon.png"),
            u"Clipper", self.iface.mainWindow())
        self.action0 = QAction( QCoreApplication.translate("Clipper", "Clip" ), self.iface.mainWindow() )
        #--->0.2 new action in plugin menu: intersection preview
        self.action1 = QAction( QCoreApplication.translate("Clipper", "Intersection Preview (Polygon)" ), self.iface.mainWindow() )
        self.action2 = QAction( QCoreApplication.translate("Clipper", "Clipping Preview (Polygon)" ), self.iface.mainWindow() )
        # connect the action to the run method
        self.action.triggered.connect(self.run)
        #--> 0.2 clip directly from menu
        self.action0.triggered.connect(self.run)
        #--->0.2  connect action to preview function
        self.action1.triggered.connect(self.preview_int)
        self.action2.triggered.connect(self.preview_clip)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        #--->0.2  add to menu action preview and clip
        self.iface.addPluginToVectorMenu(u"&Clipper", self.action0)
        self.iface.addPluginToVectorMenu(u"&Clipper", self.action1)
        self.iface.addPluginToVectorMenu(u"&Clipper", self.action2)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginVectorMenu(u"&Clipper", self.action)
        self.iface.removeToolBarIcon(self.action)
        #--->0.2  remove from menu action0 clip
        self.iface.removePluginVectorMenu(u"&Clipper", self.action0)
        #--->0.2  remove from menu action preview
        self.iface.removePluginVectorMenu(u"&Clipper", self.action1)
        self.iface.removePluginVectorMenu(u"&Clipper", self.action2)
        
#---> Custom function begin
    def checkvector(self):
        count = 0
        for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
            if layer.type() == QgsMapLayer.VectorLayer:
                count += 1
        return count

    def get_layer(self):
        layer = self.iface.mapCanvas().currentLayer()
        if layer:
            return layer 
        else:
            self.iface.messageBar().pushMessage("Clipper"," No active layer found :please click on one!", level=QgsMessageBar.CRITICAL, duration=3)
            
    def clip(self):
        #remove any intersect or clipped (preview) named layer in legend
        for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
            if (layer.name()== "Intersect" or layer.name() =="Clipped"):
                layid = layer.id()
                if layid:
                    QgsMapLayerRegistry.instance().removeMapLayer(layid)
        #close previously open messageBar
        self.iface.messageBar().popWidget()
        #clipping begin
        layer = self.get_layer()
        if layer:
            layername = layer.name()
            provider=layer.dataProvider()
            features = layer.getFeatures()
            for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
                if layer.type() == QgsMapLayer.VectorLayer:
                    if layer.name()== layername:
                        #--->Polygon handling
                        #check for layer type(polygon,multipolygon)
                        if layer.wkbType() == 3 or layer.wkbType() == 6:
                            #get feature selection
                            selection = layer.selectedFeatures()
                            if len(selection)!=0:
                                for f in layer.getFeatures():
                                    #check for geometry validity...experimental
                                    if f.geometry():
                                        if f.id() == selection[0].id():
                                            fsel = f
                                    else:
                                        self.iface.messageBar().pushMessage("Clipper","possible invalid geometry id:"+unicode(f.id()), level=QgsMessageBar.CRITICAL, duration=8)
                                if fsel:
                                    #set layer editable
                                    layer.startEditing()
                                    count = 0
                                    for g in layer.getFeatures():
                                        #check for geometry validity
                                        if g.geometry():
                                            if g.id() != fsel.id():
                                                if (g.geometry().intersects(fsel.geometry())):
                                                    #clipping non selected intersecting features
                                                    geometry = QgsGeometry.fromPolygon(g.geometry().asPolygon())
                                                    attributes = g.attributes()
                                                    diff = QgsFeature()
                                                    # Calculate the difference between the original 
                                                    # selected geometry and other features geometry only
                                                    # if the features intersects the selected geometry
                                                    #set new geometry
                                                    diff.setGeometry(g.geometry().difference(fsel.geometry()))
                                                    #copy attributes from original feature
                                                    diff.setAttributes(attributes)
                                                    #add modified feature to layer
                                                    layer.addFeature(diff)
                                                    #remove old feature
                                                    if layer.deleteFeature(g.id()):
                                                        count +=1
                                                    else:
                                                        count = 0 
                                        else:
                                            self.iface.messageBar().pushMessage("Clipper","possible invalid geometry id:"+unicode(g.id()), level=QgsMessageBar.CRITICAL, duration=7)
                                    #refresh the view and clear selection
                                    self.iface.mapCanvas().refresh()
                                    layer.setSelectedFeatures([])
                                    if count > 1:
                                        self.iface.messageBar().pushMessage("Clipper",""+str(count)+" features clipped: "+"   Remember to save your edits...", level=QgsMessageBar.INFO)
                                    else:
                                        self.iface.messageBar().pushMessage("Clipper",""+str(count)+" feature clipped: "+"   Remember to save your edits...", level=QgsMessageBar.INFO)
                            else:
                                self.iface.messageBar().pushMessage("Clipper"," Select at least one feature !", level=QgsMessageBar.CRITICAL, duration=8)
                        #--->Linestring handling
                        #check for mline or multiline type
                        elif layer.wkbType() == 2 or layer.wkbType() == 5:
                            #get the cutting line from feature selection
                            selection = layer.selectedFeatures()
                            if len(selection) != 0:
                                for f in layer.getFeatures():
                                    if f.id() == selection[0].id():
                                        fsel = f
                                    else:
                                        self.iface.messageBar().pushMessage("Clipper","possible invalid geometry id:"+unicode(f.id()), level=QgsMessageBar.CRITICAL, duration=7)
                                if fsel:
                                    #unselect all features and set layer editable
                                    layer.startEditing()
                                    layer.setSelectedFeatures([])
                                    count = 0
                                    #select features to be splitted
                                    to_be_clipped=[]
                                    for g in layer.getFeatures():
                                        if g.id() != fsel.id():
                                            if (g.geometry().intersects(fsel.geometry())):
                                                to_be_clipped.append(g.id())
                                                count+=1
                                    if to_be_clipped==[]:
                                        self.iface.messageBar().pushMessage("Clipper","Clipping is not possible because no feature intersects the given line... ", level=QgsMessageBar.CRITICAL)
                                    else:
                                        t=layer.splitFeatures(fsel.geometry().asPolyline())
                                        #refresh the view and clear selection
                                        self.iface.mapCanvas().refresh()
                                        layer.setSelectedFeatures([])
                                        if count > 1:
                                            self.iface.messageBar().pushMessage("Clipper",""+str(count)+" features split: "+"   Remember to save your edits...", level=QgsMessageBar.INFO)
                                        else:
                                            self.iface.messageBar().pushMessage("Clipper",""+str(count)+" feature split: "+"   Remember to save your edits...", level=QgsMessageBar.INFO)
                            
                            else:
                                self.iface.messageBar().pushMessage("Clipper"," Select at least one feature !", level=QgsMessageBar.CRITICAL, duration=8)
                        
    #polygon intersection preview: possibile only in polygon type layers
    def preview_int(self):
        #remove any intersect or clipped (preview) named layer in legend
        for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
            if (layer.name()== "Intersect" or layer.name() =="Clipped"):
                layid = layer.id()
                if layid:
                    QgsMapLayerRegistry.instance().removeMapLayer(layid)
        #close previously open messageBar
        self.iface.messageBar().popWidget()
        #begin intersect Preview
        layer = self.get_layer()
        if layer:
            layername = layer.name()
            provider=layer.dataProvider()
            features = layer.getFeatures()
            for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
                if layer.type() == QgsMapLayer.VectorLayer:
                    if layer.name()== layername:
                        #--->Polygon handling
                        #check for layer type
                        #debug
                        pyqtRemoveInputHook()
                        pdb.set_trace()
                        if layer.wkbType() == 3 or layer.wkbType() == 6:
                            #get feature selection
                            selection = layer.selectedFeatures()
                            if len(selection)!=0:
                                for f in layer.getFeatures():
                                    #check for geometry validity...experimental
                                    if f.geometry():
                                        if f.id() == selection[0].id():
                                            fsel = f
                                    else:
                                        self.iface.messageBar().pushMessage("Clipper","possible invalid geometry id:"+unicode(f.id()), level=QgsMessageBar.CRITICAL, duration=7)
                                if fsel:
#                                    pyqtRemoveInputHook()#debug
#                                    pdb.set_trace() #debug
                                    count = 0
                                    # Create a memory layer to store the result setting an initial crs
                                    # to avoid qgis from asking which crs or type of new vector layer
                                    if layer.wkbType() == 6:
                                        resultl = QgsVectorLayer("MultiPolygon?crs=EPSG:4326", "Intersect", "memory")
                                    else:
                                        resultl = QgsVectorLayer("Polygon?crs=EPSG:4326", "Intersect", "memory")
                                    #change memorylayer crs to layer crs initilize data and start editing
                                    resultl.setCrs(layer.crs()) 
                                    resultpr = resultl.dataProvider()
                                    resultl.startEditing()
                                    #add memorylayer to canvas
                                    QgsMapLayerRegistry.instance().addMapLayer(resultl)
                                    for g in layer.getFeatures():
                                        #check for geometry validity
                                        if g.geometry():
                                            if g.id() != fsel.id():
                                                #check for geometry type
                                                type = g.geometry().wkbType()
                                                if (g.geometry().intersects(fsel.geometry())):
                                                    #choose non selected intersecting features checkin multi-Polygon
                                                    if type == 6:
                                                       geometry = QgsGeometry.fromMultiPolygon(g.geometry().asMultiPolygon())
                                                    else:
                                                       geometry = QgsGeometry.fromPolygon(g.geometry().asPolygon())
                                                    attributes = g.attributes()
                                                    inters = QgsFeature()
                                                    # Calculate the difference between the original 
                                                    # selected geometry and other features geometry only
                                                    # if the features intersects the selected geometry
                                                    #set new geometry
                                                    inters.setGeometry(g.geometry().intersection(fsel.geometry()))
                                                    #copy attributes from original feature
                                                    inters.setAttributes(attributes)
                                                    #add modified feature to memory layer
                                                    resultpr.addFeatures([inters])
                                                    count+=1
                                                    resultl.commitChanges()
                                                    #type = None
                                        else:
                                            self.iface.messageBar().pushMessage("Clipper","possible invalid geometry id:"+unicode(g.id()), level=QgsMessageBar.CRITICAL, duration=7)
                                    #refresh the view
                                    self.iface.mapCanvas().refresh()
                                    #output messages
                                    if count > 1:
                                        widget = self.iface.messageBar().createMessage("Intersecting preview of "+str(count)+" features. To clip features click on the button:", "Clip")
                                        button = QPushButton(widget)
                                        button.setText("Clip")
                                        button.pressed.connect(self.clip)
                                        widget.layout().addWidget(button)
                                        self.iface.messageBar().pushWidget(widget, QgsMessageBar.INFO)
                                        resultl.commitChanges()
                                    else:
                                        widget = self.iface.messageBar().createMessage("Intersecting preview "+str(count)+" feature. To clip feature click on the button:", "Clip")
                                        button = QPushButton(widget)
                                        button.setText("Clip")
                                        button.pressed.connect(self.clip)
                                        widget.layout().addWidget(button)
                                        self.iface.messageBar().pushWidget(widget, QgsMessageBar.INFO)
                            else:
                                self.iface.messageBar().pushMessage("Clipper"," Select at least one feature !", level=QgsMessageBar.CRITICAL, duration=8)
                        else:
                            self.iface.messageBar().pushMessage("Clipper"," Wrong type of layer to perform intersection preview, sorry ..." , level=QgsMessageBar.CRITICAL, duration=8)    

    #polygon clipping preview
    def preview_clip(self):
        layer = self.get_layer()
        if layer:
            layername = layer.name()
            provider=layer.dataProvider()
            features = layer.getFeatures()
            for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
                if layer.type() == QgsMapLayer.VectorLayer:
                    if layer.name()== layername:
                        #--->Polygon handling
                        #check for layer type compatibility
                        if layer.wkbType() == 3 or layer.wkbType() == 6:
                            #get feature selection
                            selection = layer.selectedFeatures()
                            if len(selection)!=0:
                                for f in layer.getFeatures():
                                    #check for geometry validity
                                    if f.geometry():
                                        if f.id() == selection[0].id():
                                            fsel = f
                                    else:
                                        self.iface.messageBar().pushMessage("Clipper","possible invalid geometry id:"+unicode(f.id()), level=QgsMessageBar.CRITICAL)
                                if fsel:
                                    count = 0
                                    # Create a memory layer to store the result setting an initial crs
                                    # to avoid qgis from asking which crs or type of new vector layer
                                    if layer.wkbType() == 6:
                                        resultl = QgsVectorLayer("MultiPolygon?crs=EPSG:4326", "Intersect", "memory")
                                    elif layer.wkbType() == 3:
                                        resultl = QgsVectorLayer("Polygon?crs=EPSG:4326", "Intersect", "memory")
                                    #change memorylayer crs to match layer crs
                                    resultl.setCrs(layer.crs()) 
                                    resultpr = resultl.dataProvider()
                                    #add memorylayer to canvas
                                    QgsMapLayerRegistry.instance().addMapLayer(resultl)
                                    for g in layer.getFeatures():
                                        #check for geometry validity...experimental
                                        if g.geometry():
                                            if g.id() != fsel.id():
                                                if (g.geometry().intersects(fsel.geometry())):
                                                #choose non selected intersecting features
                                                    geometry = QgsGeometry.fromPolygon(g.geometry().asPolygon())
                                                    attributes = g.attributes()
                                                    clipped = QgsFeature()
                                                    # Calculate the difference between the original 
                                                    # selected geometry and other features geometry only
                                                    # if the features intersects the selected geometry
                                                    #set new geometry
                                                    clipped.setGeometry(g.geometry().difference(fsel.geometry()))
                                                    #copy attributes from original feature
                                                    clipped.setAttributes(attributes)
                                                    #add modified feature to memory layer
                                                    resultpr.addFeatures([clipped])
                                                    count+=1
                                        else:
                                            self.iface.messageBar().pushMessage("Clipper","possible invalid geometry id:"+unicode(g.id()), level=QgsMessageBar.CRITICAL)
                                    #refresh the view
                                    self.iface.mapCanvas().refresh()
                                    #output messages
                                    if count > 1:
                                        widget = self.iface.messageBar().createMessage("Clipping preview of "+str(count)+" features. To clip features click on the button:", "Clip")
                                        button = QPushButton(widget)
                                        button.setText("Clip")
                                        button.pressed.connect(self.clip)
                                        widget.layout().addWidget(button)
                                        self.iface.messageBar().pushWidget(widget, QgsMessageBar.INFO)
                                    else:
                                        widget = self.iface.messageBar().createMessage("Clipping preview "+str(count)+" feature. To clip feature click on the button:", "Clip")
                                        button = QPushButton(widget)
                                        button.setText("Clip")
                                        button.pressed.connect(self.clip)
                                        widget.layout().addWidget(button)
                                        self.iface.messageBar().pushWidget(widget, QgsMessageBar.INFO)
                            else:
                                self.iface.messageBar().pushMessage("Clipper"," Select at least one feature !", level=QgsMessageBar.CRITICAL, duration=7)
                        else:
                            self.iface.messageBar().pushMessage("Clipper"," Wrong type of layer to perform cillping preview, sorry ..." , level=QgsMessageBar.CRITICAL, duration=7)        
#---> Custom functions end 
    # run method that performs all the real work
    def run(self):
        check = 0
        check = self.checkvector()
        if check == 0:
            self.iface.messageBar().pushMessage("Clipper"," No Vector layer found !",level=QgsMessageBar.CRITICAL)
            #QMessageBox.critical(None, "Critical","No vector layers \n Please load some, then reload plugin")
            pass
        else:
            self.clip()
            
        # show the dialog
        #self.dlg.show()
        # Run the dialog event loop
        #result = self.dlg.exec_()
        # See if OK was pressed
        #if result == 1:
            # do something useful (delete the line containing pass and
            # substitute with your code)
            #pass
