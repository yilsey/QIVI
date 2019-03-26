# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QIVI
                                 A QGIS plugin
 Plugin para el cálculo del Índice de Valor de Importancia (IVI)
                             -------------------
        begin                : 2018-04-29
        copyright            : (C) 2018 by Karen Huertas - Yilsey Benavides (Universidad Distrital Francisco José de Caldas)
        email                : karenahva@gmail.com - yilmiranda@gmail.com
        git sha              : $Format:%H$
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


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load QIVI class from file QIVI.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    """
    #
    from .QIVI import QIVI
    return QIVI(iface)
