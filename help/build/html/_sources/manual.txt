Clipper Plugin Manual Ver. 0.2.1
================================

2014 © Giuseppe De Marco 

The clipper plugin is a python plugin that performs a missing feature of current (2.2) Qgis Version:
clipping of features inside the same shapefile from a selected feature (line or polygon).
Polygon clipping from a selected polygon feature clips all intersecting features and returns clipped features with the same attributes deleting old ones: do not worry you have to confirm your edits by saving edits for the layer manually!
Linestring clipping should be considered as trim/split feature: it takes as cutting line a selected line from active layer and split all intersecting lines. After the splitting you will have the chance to manually delete unwanted split parts.  

Usage
'''''
1) Set a layer active and select a clipping/cutting feature (line or polygon) otherwise the plugin will complain about no active layer found or no selected feature ...

2) Click on the plugin button in plugins toolbar or access :guilabel:`Clipper` plugin, going to :menuselection:`Vector -->Clipper --> Clipper`.

3) Check  for the result in Map Canvas and if it is satisfactory save edits.


Preview (for polygons only)
'''''''''''''''''''''''''''

1.1) Set a layer active and select a clipping/cutting feature otherwise the plugin will complain about no active layer found or no selected feature...

2.1) Access :guilabel:`Clipper` plugin, going to :menuselection:`Vector -->Clipper --> Intersection Preview` and you will be shown a new memory layer in legend with the intersecting polygon parts 

2.2) Access :guilabel:`Clipper` plugin, going to :menuselection:`Vector -->Clipper --> Clipping Preview` and you will be shown a new memory layer in legend with the clipped polygons  

3.1) If the result is fair enough you can either close the message widget and run Clipper plugin either push 'Clip' button in the widget: this will fire up the clipping process anyway...

4.1) Remember to save your edits if you wish to keep modifications.

Any contribution is most appreciated.

Giuseppe De Marco
