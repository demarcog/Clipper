# -*- coding: utf-8 -*-
"""
/***************************************************************************
 clipper
                                 A QGIS plugin
 This plugin lets you use clipping function in the same shapefile selecting a line or polygon clips all overlaying features
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
 This script initializes the plugin, making it known to QGIS.
"""

def classFactory(iface):
    # load clipper class from file clipper
    from clipper import clipper
    return clipper(iface)
