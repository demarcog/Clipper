# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clipper
                                 A QGIS plugin
 This plugin lets you use clipping function in the same shapefile selecting
  a line or polygon clips all overlaying features
                              -------------------
        begin                : 2014-06-27
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
        #--->0.2 new action in plugin menu: intersection preview
        self.action1 = QAction( QCoreApplication.translate("Clipper", "Intersection Preview" ), self.iface.mainWindow() )
        # connect the action to the run method
        #--->0.2 insert new action in plugin menu for the preview!!!!!
        self.action.triggered.connect(self.run)
        #--->0.2  connect action to preview function
        self.action1.triggered.connect(self.preview)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu(u"&Clipper", self.action)
        #--->0.2  add to menu action preview
        self.iface.addPluginToVectorMenu(u"&Clipper", self.action1)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginVectorMenu(u"&Clipper", self.action)
        self.iface.removeToolBarIcon(self.action)
        #--->0.2  add to menu action preview
        self.iface.removePluginVectorMenu(u"&Clipper", self.action1)
        
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
        #0.2 version check if there a result named layer in legend and remove it
        for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
            if layer.name()== "Intersect":
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
                        #check for layer type
                        if layer.wkbType() == QGis.WKBPolygon:
                            #get feature selection
                            selection = layer.selectedFeatures()
                            if len(selection)!=0:
                                for f in layer.getFeatures():
                                    if f.id() == selection[0].id():
                                        fsel = f
                                if fsel:
                                    #set layer editable
                                    layer.startEditing()
                                    count = 0
                                    for g in layer.getFeatures():
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
                                    #refresh the view and clear selection
                                    self.iface.mapCanvas().refresh()
                                    layer.setSelectedFeatures([])
                                    if count > 1:
                                        self.iface.messageBar().pushMessage("Clipper",""+str(count)+" features clipped: "+"   Remember to save your edits...", level=QgsMessageBar.INFO)
                                    else:
                                        self.iface.messageBar().pushMessage("Clipper",""+str(count)+" feature clipped: "+"   Remember to save your edits...", level=QgsMessageBar.INFO)
                            else:
                                self.iface.messageBar().pushMessage("Clipper"," Select at least one feature !", level=QgsMessageBar.CRITICAL, duration=4)
                        #--->Linestring handling
                        #A bit of working is needed for LineString objects...
                        elif layer.wkbType() == QGis.WKBLineString:
                            #self.iface.messageBar().pushMessage("Clipper"," Line type layer found: clip function works as a line splitter: one has to manually delete wanted clipped parts...", level=QgsMessageBar.WARNING, duration=5)
                            #get the cutting line from feature selection
                            selection = layer.selectedFeatures()
                            if len(selection) != 0:
                                for f in layer.getFeatures():
                                    if f.id() == selection[0].id():
                                        fsel = f
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
                                self.iface.messageBar().pushMessage("Clipper"," Select at least one feature !", level=QgsMessageBar.CRITICAL, duration=4)
#---> 0.2 new feature: polygon intersection preview
    def preview(self):
        layer = self.get_layer()
        if layer:
            #self.iface.messageBar().pushMessage("Clipper"," Vector layer found", level=QgsMessageBar.INFO, duration=5)
            layername = layer.name()
            provider=layer.dataProvider()
            features = layer.getFeatures()
            for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
                if layer.type() == QgsMapLayer.VectorLayer:
                    if layer.name()== layername:
                        #--->Polygon handling
                        #check for layer type
                        if layer.wkbType() == QGis.WKBPolygon:
                            #get feature selection
                            selection = layer.selectedFeatures()
                            if len(selection)!=0:
                                for f in layer.getFeatures():
                                    if f.id() == selection[0].id():
                                        fsel = f
                                if fsel:
                                    count = 0
                                    # Create a memory layer to store the result setting an initial crs
                                    #to avoid qgis from asking
                                    resultl = QgsVectorLayer("Polygon?crs=EPSG:4326", "Intersect", "memory")
                                    #change memorylayer crs to layer crs
                                    resultl.setCrs(layer.crs()) 
                                    resultpr = resultl.dataProvider()
                                    #add memorylayer to canvas
                                    QgsMapLayerRegistry.instance().addMapLayer(resultl)
                                    for g in layer.getFeatures():
                                        if g.id() != fsel.id():
                                            if (g.geometry().intersects(fsel.geometry())):
                                                #choose non selected intersecting features
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
                                    else:
                                        widget = self.iface.messageBar().createMessage("Intersecting preview "+str(count)+" feature. To clip feature click on the button:", "Clip")
                                        button = QPushButton(widget)
                                        button.setText("Clip")
                                        button.pressed.connect(self.clip)
                                        widget.layout().addWidget(button)
                                        self.iface.messageBar().pushWidget(widget, QgsMessageBar.INFO)
                            else:
                                self.iface.messageBar().pushMessage("Clipper"," Select at least one feature !", level=QgsMessageBar.CRITICAL, duration=4)
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
