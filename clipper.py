# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clipper
                                 A QGIS plugin
 This plugin lets you use clipping function in the same shapefile selecting
  a line or polygon clips all overlaying features
                              -------------------
        begin                : 2014-06-27
        new version      : 2018-04-19 
        copyright            : (C) 2018 by Giuseppe De Marco
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
from __future__ import absolute_import
from builtins import str
from builtins import object
from qgis.core import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtXml import *
# Initialize Qt resources from file resources.py
from . import resources_rc
# Import the code for the dialog
#from clipperdialog import clipperDialog
import os.path


class clipper(object):

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
        for name, layer in list(QgsProject.instance().mapLayers().items()):
            if layer.type() == QgsMapLayer.VectorLayer:
                count += 1
        return count

    def get_layer(self):
        layer = self.iface.mapCanvas().currentLayer()
        if layer:
            return layer 
        else:
            self.iface.messageBar().pushMessage("Clipper"," No active layer found :please click on one!", level=Qgis.Critical, duration=3)
            
    def clip(self):
        #0.2 version check if there a intersect or clipped (preview) named layer in legend and remove it
        for name, layer in list(QgsProject.instance().mapLayers().items()):
            if (layer.name()== "Intersect" or layer.name() =="Clipped"):
                layid = layer.id()
                if layid:
                    QgsProject.instance().removeMapLayer(layid)
        #close previously open messageBar
        self.iface.messageBar().popWidget()
        #clipping begin
        layer = self.get_layer()
        if layer:
            layername = layer.name()
            provider=layer.dataProvider()
            features = layer.getFeatures()
            for name, layer in list(QgsProject.instance().mapLayers().items()):
                if layer.type() == QgsMapLayer.VectorLayer:
                    if layer.name()== layername:
                        #--->Polygon handling
                        #check for layer type
                        if layer.wkbType() ==2 or 6:
                            #get feature selection
                            selection = layer.selectedFeatures()
                            if len(selection)!=0:
                                for f in layer.getFeatures():
                                    #check for geometry validity...experimental
                                    if f.geometry():
                                        if f.id() == selection[0].id():
                                            fsel = f
                                    else:
                                        self.iface.messageBar().pushMessage("Clipper","possible invalid geometry id:"+str(f.id()), level=Qgis.Critical, duration=7)
                                if fsel:
                                    #set layer editable
                                    layer.startEditing()
                                    count = 0
                                    for g in layer.getFeatures():
                                        #check for geometry validity...experimental
                                        if g.geometry():
                                            if g.id() != fsel.id():
                                                if (g.geometry().intersects(fsel.geometry())):
                                                    #clipping non selected intersecting features
                                                    geometry = QgsGeometry.fromPolygonXY(g.geometry().asPolygon())
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
                                            self.iface.messageBar().pushMessage("Clipper","possible invalid geometry id:"+str(g.id()), level=Qgis.Critical, duration=7)
                                    #refresh the view and clear selection
                                    self.iface.mapCanvas().refresh()
                                    self.iface.mapCanvas().currentLayer().selectAll()
                                    self.iface.mapCanvas().currentLayer().invertSelection()
                                    if count > 1:
                                        self.iface.messageBar().pushMessage("Clipper",""+str(count)+" features clipped: "+"   Remember to save your edits...", level=Qgis.Info)
                                    else:
                                        self.iface.messageBar().pushMessage("Clipper",""+str(count)+" feature clipped: "+"   Remember to save your edits...", level=Qgis.Info)
                            else:
                                self.iface.messageBar().pushMessage("Clipper"," Select at least one feature !", level=Qgis.Critical, duration=4)
                        #--->Linestring handling
                        #A bit of working is needed for LineString objects...
                        elif layer.wkbType() == 1:
                            #self.iface.messageBar().pushMessage("Clipper"," Line type layer found: clip function works as a line splitter: one has to manually delete wanted clipped parts...", level=QgsMessageBar.WARNING, duration=5)
                            #get the cutting line from feature selection
                            selection = layer.selectedFeatures()
                            if len(selection) != 0:
                                for f in layer.getFeatures():
                                    if f.id() == selection[0].id():
                                        fsel = f
                                    else:
                                        self.iface.messageBar().pushMessage("Clipper","possible invalid geometry id:"+str(f.id()), level=Qgis.Critical, duration=7)
                                if fsel:
                                    #unselect all features and set layer editable
                                    layer.startEditing()
                                    self.iface.mapCanvas().currentLayer().selectAll()
                                    self.iface.mapCanvas().currentLayer().invertSelection()
                                    count = 0
                                    #select features to be splitted
                                    to_be_clipped=[]
                                    for g in layer.getFeatures():
                                        if g.id() != fsel.id():
                                            if (g.geometry().intersects(fsel.geometry())):
                                                to_be_clipped.append(g.id())
                                                count+=1
                                    if to_be_clipped==[]:
                                        self.iface.messageBar().pushMessage("Clipper","Clipping is not possible because no feature intersects the given line... ", level=Qgis.Critical)
                                    else:
                                        t=layer.splitFeatures(fsel.geometry().asPolyline())
                                        #refresh the view and clear selection
                                        self.iface.mapCanvas().refresh()
                                        self.iface.mapCanvas().currentLayer().selectAll()
                                        self.iface.mapCanvas().currentLayer().invertSelection()
                                        if count > 1:
                                            self.iface.messageBar().pushMessage("Clipper",""+str(count)+" features split: "+"   Remember to save your edits...", level=Qgis.Info)
                                        else:
                                            self.iface.messageBar().pushMessage("Clipper",""+str(count)+" feature split: "+"   Remember to save your edits...", level=Qgis.Info)
                            
                            else:
                                self.iface.messageBar().pushMessage("Clipper"," Select at least one feature !", level=Qgis.Critical, duration=4)
#---> 0.2 new feature: polygon intersection preview
    def preview_int(self):
        layer = self.get_layer()
        if layer:
            #self.iface.messageBar().pushMessage("Clipper"," Vector layer found", level=Qgis.Info, duration=5)
            layername = layer.name()
            provider=layer.dataProvider()
            features = layer.getFeatures()
            for name, layer in list(QgsProject.instance().mapLayers().items()):
                if layer.type() == QgsMapLayer.VectorLayer:
                    if layer.name()== layername:
                        #--->Polygon handling
                        #check for layer type
                        if layer.wkbType() == 2 or 6:
                            #get feature selection
                            selection = layer.selectedFeatures()
                            if len(selection)!=0:
                                for f in layer.getFeatures():
                                    #check for geometry validity...experimental
                                    if f.geometry():
                                        if f.id() == selection[0].id():
                                            fsel = f
                                    else:
                                        self.iface.messageBar().pushCritical("Clipper","possible invalid geometry id:"+str(f.id()))
                                if fsel:
                                    count = 0
                                    # Create a memory layer to store the result setting an initial crs
                                    #to avoid qgis from asking
                                    resultl = QgsVectorLayer("Polygon?crs=EPSG:4326", "Intersect", "memory")
                                    #change memorylayer crs to layer crs
                                    resultl.setCrs(layer.crs()) 
                                    resultpr = resultl.dataProvider()
                                    #add memorylayer to canvas
                                    QgsProject.instance().addMapLayer(resultl)
                                    for g in layer.getFeatures():
                                        #check for geometry validity...experimental
                                        if g.geometry():
                                            if g.id() != fsel.id():
                                                if (g.geometry().intersects(fsel.geometry())):
                                                    #choose non selected intersecting features
                                                    geometry = QgsGeometry.fromPolygonXY(g.geometry().asPolygon())
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
                                        else:
                                            self.iface.messageBar().pushCritical("Clipper","possible invalid geometry id:"+str(g.id()))
                 
                                    #refresh the view
                                    self.iface.mapCanvas().refresh()
                                    #output messages
                                    if count > 1:
                                        widget = self.iface.messageBar().createMessage("Intersecting preview of "+str(count)+" features. To clip features click on the button:", "Clip")
                                        button = QPushButton(widget)
                                        button.setText("Clip")
                                        button.pressed.connect(self.clip)
                                        widget.layout().addWidget(button)
                                        self.iface.messageBar().pushWidget(widget, Qgis.Info)
                                    else:
                                        widget = self.iface.messageBar().createMessage("Intersecting preview "+str(count)+" feature. To clip feature click on the button:", "Clip")
                                        button = QPushButton(widget)
                                        button.setText("Clip")
                                        button.pressed.connect(self.clip)
                                        widget.layout().addWidget(button)
                                        self.iface.messageBar().pushWidget(widget, Qgis.Info)
                            else:
                                self.iface.messageBar().pushMessage("Clipper"," Select at least one feature !")
#---> 0.2 new feature: polygon clipping preview
    def preview_clip(self):
        layer = self.get_layer()
        if layer:
            layername = layer.name()
            provider=layer.dataProvider()
            features = layer.getFeatures()
            for name, layer in list(QgsProject.instance().mapLayers().items()):
                if layer.type() == QgsMapLayer.VectorLayer:
                    if layer.name()== layername:
                        #--->Polygon handling
                        #check for layer type
                        if layer.wkbType() == 2 or 6:
                            #get feature selection
                            selection = layer.selectedFeatures()
                            if len(selection)!=0:
                                for f in layer.getFeatures():
                                    #check for geometry validity...experimental
                                    if f.geometry():
                                        if f.id() == selection[0].id():
                                            fsel = f
                                    else:
                                        self.iface.messageBar().pushCritical("Clipper","possible invalid geometry id:"+str(f.id()))
                                if fsel:
                                    count = 0
                                    # Create a memory layer to store the result setting an initial crs
                                    #to avoid qgis from asking
                                    resultl = QgsVectorLayer("Polygon?crs=EPSG:4326", "Clipped", "memory")
                                    #change memorylayer crs to layer crs
                                    resultl.setCrs(layer.crs()) 
                                    resultpr = resultl.dataProvider()
                                    #add memorylayer to canvas
                                    QgsProject.instance().addMapLayer(resultl)
                                    for g in layer.getFeatures():
                                        #check for geometry validity...experimental
                                        if g.geometry():
                                            if g.id() != fsel.id():
                                                if (g.geometry().intersects(fsel.geometry())):
                                                #choose non selected intersecting features
                                                    geometry = QgsGeometry.fromPolygonXY(g.geometry().asPolygon())
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
                                            self.iface.messageBar().pushMessage("Clipper","possible invalid geometry id:"+str(g.id()), level=Qgis.Critical)
                                    #refresh the view
                                    self.iface.mapCanvas().refresh()
                                    #output messages
                                    if count > 1:
                                        widget = self.iface.messageBar().createMessage("Clipping preview of "+str(count)+" features. To clip features click on the button:", "Clip")
                                        button = QPushButton(widget)
                                        button.setText("Clip")
                                        button.pressed.connect(self.clip)
                                        widget.layout().addWidget(button)
                                        self.iface.messageBar().pushWidget(widget, Qgis.Info)
                                    else:
                                        widget = self.iface.messageBar().createMessage("Clipping preview "+str(count)+" feature. To clip feature click on the button:", "Clip")
                                        button = QPushButton(widget)
                                        button.setText("Clip")
                                        button.pressed.connect(self.clip)
                                        widget.layout().addWidget(button)
                                        self.iface.messageBar().pushWidget(widget, Qgis.Info)
                            else:
                                self.iface.messageBar().pushMessage("Clipper"," Select at least one feature !", level=Qgis.Critical, duration=4)
#---> Custom functions end 
    # run method that performs all the real work
    def run(self):
        check = 0
        check = self.checkvector()
        if check == 0:
            self.iface.messageBar().pushMessage("Clipper"," No Vector layer found !",level=Qgis.Critical)
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
