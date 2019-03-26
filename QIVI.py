# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QIVI
                                 A QGIS plugin
 Plugin para el cálculo del Índice de Valor de Importancia (IVI)
                              -------------------
        begin                : 2018-04-29
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Karen Huertas - Yilsey Benavides (Universidad Distrital Francisco José de Caldas)
        email                : karenahva@gmail.com - yilmiranda@gmail.com
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon
from PyQt4.QtGui import QMessageBox, QLineEdit
from PyQt4.QtCore import QVariant
from PyQt4.QtCore import Qt
from PyQt4 import QtGui, uic
from PyQt4 import QtCore, QtGui
from processing.algs.gdal.OgrAlgorithm import OgrAlgorithm
from processing.algs.gdal.GdalUtils import GdalUtils

from processing.tools.vector import TableWriter
from collections import defaultdict
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
import collections
import math
import processing
import os
from qgis.gui import QgsMessageBar
from os import path
from qgis.core import *
from qgis.gui import *
from qgis.core import QgsProject
import csv
import tempfile

import resources

from QIVI_dialog import QIVIDialog
import os.path

class QIVI:
    """QGIS Plugin Implementation."""
    layers=0
    nombreCC=0
    a_capaEntrada=0
    areaBasal=0
    parcela= 0

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgisInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.layers = self.iface.legendInterface().layers()
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'QIVI_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&QIVI')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'QIVI')
        self.toolbar.setObjectName(u'QIVI')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('QIVI', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference


        self.dlg = QIVIDialog()
        self.layers = self.iface.legendInterface().layers()
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def selected(self):
        index_capaentrada = self.dlg.capaEntrada.currentIndex()
        selected_ce = self.layers[index_capaentrada]
        self.a_capaEntrada=selected_ce
        fieldsCapa = selected_ce.pendingFields()
        fieldnamesCapaEntrada = [field.name() for field in fieldsCapa]
        self.dlg.nombreCC.clear()
        self.dlg.nombreCC.addItems(fieldnamesCapaEntrada)
        self.dlg.areaBasal.clear()
        self.dlg.areaBasal.addItems(fieldnamesCapaEntrada)
        self.dlg.parcela.clear()
        self.dlg.parcela.addItems(fieldnamesCapaEntrada)

    def campos(self):

        self.nombreCC=self.dlg.nombreCC.currentText()
        self.areaBasal=self.dlg.areaBasal.currentText()
        self.parcela=self.dlg.parcela.currentText()

    def tabla(self):

       lista=[]
       campo_familia =[QgsField( 'ID', QVariant.Int)]
       res=self.a_capaEntrada.dataProvider()
       ########### Carga los datos en arreglos ##########
       p = res.getFeatures() # lee los datos
       count = len( [f for f in p] )
       InputAreaBasal = []
       InputParcela = []
       p = res.getFeatures()
       for Feature in p:
            pElemArea = (Feature[self.areaBasal], Feature[self.nombreCC])
            InputAreaBasal.append(pElemArea)
            pElemParcela = (Feature[self.parcela], Feature[self.nombreCC])
            InputParcela.append(pElemParcela)
       resAgruparArea = defaultdict(list)
       for v, k in InputAreaBasal: resAgruparArea[k].append(v)
       ResultadoAgupArea = [{'type':k, 'items':v} for k,v in resAgruparArea.items()]

       resAgruparParcela = defaultdict(list)
       for v, k in InputParcela: resAgruparParcela[k].append(v)
       ResultadoAgupParcela = [{'type':k, 'items':v} for k,v in resAgruparParcela.items()]
       SumAreasBasales = 0
       for iArea in InputAreaBasal:
            SumAreasBasales = SumAreasBasales + iArea[0]

       pContador = 1
       pTablaRes = defaultdict(list)
       pSumFrecAbs = 0
       for (pDicParcela) in ResultadoAgupParcela:
            pRegistro = []
            pArregloParcela= pDicParcela.values()[0]
            pSumFrecAbs = pSumFrecAbs + len(collections.Counter(pArregloParcela))
       for (pDic, pDicParcela) in zip(ResultadoAgupArea, ResultadoAgupParcela):
            pRegistro = []
            pArregloParcela= pDicParcela.values()[0]

            pArregloAreas = pDic.values()[0]
            pNombre = pDic.values()[1]
            suma=0
            for i in pArregloAreas:
                suma=suma + float(i)
            pContador = pContador + 1
            pAbundaciaAbsoluta = len(pArregloAreas)
            pRegistro.append(str(pContador))
            pRegistro.append(pNombre)
            pRegistro.append(pAbundaciaAbsoluta)
            pRegistro.append(suma)
            pFrecuenciaAbsoluta = len(collections.Counter(pArregloParcela))
            pRegistro.append(pFrecuenciaAbsoluta)
            pDominRelativa = (suma/SumAreasBasales)*100
            pRegistro.append(pDominRelativa)
            pAbunRelativa = (float(pAbundaciaAbsoluta)/count)*100
            pRegistro.append(pAbunRelativa)
            pFrecRelativa = (float(len(collections.Counter(pArregloParcela)))/pSumFrecAbs)*100
            pRegistro.append(pFrecRelativa)
            pRegistro.append(pFrecRelativa + pAbunRelativa + pDominRelativa)

            lista.append(pRegistro)
            pTablaRes[pNombre] = pRegistro
       pArbolMayor = sorted(pTablaRes.iteritems(),key=lambda (k,v): v[8],reverse=True)
       dire=tempfile.gettempdir()
       archivo=dire+"IVI.csv"
       pLayer = self.a_capaEntrada
       pQuery = self.nombreCC + " = '" + pArbolMayor[0][0] + "'"

       pLayer.selectByExpression(pQuery)
       with open(archivo,'w') as f:
          writer = csv.writer(f, delimiter=',')
          writer.writerow(["ID","Nombre","Abundancia_Absoluta","Area_Basal_SP","Frecuencia_Absoluta","Dominancia_Relativa","Abundancia_relativa", "Frecuencia_Relativa", "IVI"])
          writer.writerows(lista)

       archi = "file:///"
       line = archivo.replace("\\","//")
       line=line.replace("//","/")
       archi2=archi+line+"?delimiter=%s"

       uri = archi2 % (",")
       lyr = QgsVectorLayer(uri, 'QIVI','delimitedtext')
       QgsMapLayerRegistry.instance().addMapLayer(lyr)


    def cancelar_clicked(self):
            self.dlg.close()

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/QIVI/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'QIVI'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def layerChanged(self):
         registry = QgsMapLayerRegistry.instance()
         identifier =str(self.dlg.ui.indivCombo.itemData(self.dlg.ui.indivCombo.currentIndex()))
         self.indivLayer = registry.mapLayer(identifier)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&QIVI'),
                action)
            self.iface.removeToolBarIcon(action)

        del self.toolbar

    def run(self):
        """Run method that performs all the real work"""

        self.layers = QgsMapLayerRegistry.instance().mapLayers().values()
        layer_list = []

        for layer in self.layers:
           layerType = layer.type()
           if layerType == QgsMapLayer.VectorLayer:
               layer_list.append(layer.name())
           else:
               layer_list.append(layer.name())

        self.dlg.capaEntrada.addItems(layer_list)
        self.selected()

        self.dlg.capaEntrada.currentIndexChanged.connect(self.selected)
        self.campos()

        self.dlg.nombreCC.currentIndexChanged.connect(self.campos)
        self.dlg.areaBasal.currentIndexChanged.connect(self.campos)
        self.dlg.parcela.currentIndexChanged.connect(self.campos)

        self.dlg.calcular.clicked.connect(self.tabla)
        self.dlg.cancelar.clicked.connect(self.cancelar_clicked)


        self.dlg.show()

