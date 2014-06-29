Clipper Plugin Manual
=====================

2014 © Giuseppe De Marco 

The clipper plugin is a python plugins that performs a missing feature of current (2.2) Qgis Version:
clipping of features inside the same shapefile from a selected feature (line or polygon).
Polygon clipping from a selected polygon features clips all intersecting features and returns clipped features with the same attributes deleting old ones: do not worry you have to confirm your edits by saving edits for the layer manually!
Linestring clipping should be considered as trim/split feature: it takes as cutting line a selected line from active layer and split all intersecting lines. After the splitting you will have the chance to manually delete unwanted split parts.  

Usage
'''''
1) Set a layer active and select a clipping/cutting feature otherwise the plugin will complain about no active layer found or no selected feature found.

2) Click on the plugin button in plugins toolbar or access :guilabel:`Clipper` plugin, going to :menuselection:`Plugins -->Clipper --> Clipper`.

3) Check  for the result in Map Canvas and if it is satisfactory save edits.

Any contribution is most appreciated.

Giuseppe De Marco
