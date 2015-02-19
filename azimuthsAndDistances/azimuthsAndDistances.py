# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        Calculator
# Purpose:
#
# Author:      Luiz Andrade - luiz.claudio@dsg.eb.mil.br
#
# Created:     24/09/2014
# Copyright:   (c) luiz 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

import math

from ui_azimuthsAndDistances import Ui_Dialog

import memorialGenerator

class AzimuthsAndDistancesDialog( QDialog, Ui_Dialog ):
    """Class that calculates azimuths and distances among vertexes in a linestring.
    """
    def __init__(self, iface, geometry):
        """Constructor.
        """
        QDialog.__init__( self )
        self.setupUi( self )

        self.geom = geometry
        self.iface = iface
        self.points = None
        self.distancesAndAzimuths = None
        self.area = self.geom.area()
        
        # Connecting SIGNAL/SLOTS for the Output button
        QObject.connect(self.calculateButton, SIGNAL("clicked()"), self.fillTextEdit)
        
        # Connecting SIGNAL/SLOTS for the Output button
        QObject.connect(self.clearButton, SIGNAL("clicked()"), self.clearTextEdit)

        # Connecting SIGNAL/SLOTS for the Output button
        QObject.connect(self.saveFilesButton, SIGNAL("clicked()"), self.saveFiles)
        
        self.lineEdit.setInputMask("#00.00000")
        
    def setClockWiseRotation(self, points):
        n = len(points)
        count = 0
        for i in xrange(n):
            j = (i+1)%n
            k = (i+2)%n
            z = (points[j].x() - points[i].x())*(points[k].y() - points[j].y())
            z -= (points[j].y() - points[i].y())*(points[k].x() - points[j].x())
            if z < 0:
                count -= 1
            elif z > 0:
                count += 1
                
        if count > 0: #Is counter clockwise and we should revert it
            points = points[::-1]

        return points
    
    def setFirstPointToNorth(self, coords, yMax):
        if coords[0].y() == yMax:
            return coords
        
        coords.pop()
        firstPart = []
        for i in range(len(coords)):
            firstPart.append(coords[i])
            if coords[i].y() == yMax:
                break
            
        return coords[i:] + firstPart

    def saveFiles(self):
        if (not self.distancesAndAzimuths) or (not self.points):
            QMessageBox.information(self.iface.mainWindow(), self.tr("Warning!"), self.tr("Click on calculate button first to generate the needed data."))
        else:
            confrontingList = list()
            for i in xrange(self.tableWidget.rowCount()):
                item = self.tableWidget.item(i, 7)
                confrontingList.append(item.text())
                
            d = memorialGenerator.MemorialGenerator(self.lineEdit.text(), self.tableWidget, self.area, self.perimeter)
            d.exec_()
        
    def isValidType(self):
        """Verifies the geometry type.
        """
        if self.geom.isMultipart():
            QMessageBox.information(self.iface.mainWindow(), self.tr("Warning!"), self.tr("The limit of a patrimonial area must be a single part geometry."))
            return False

        if self.geom.type() == QGis.Line:
            self.points = self.geom.asPolyline()
            if self.points[0].y() < self.points[-1].y():
                self.points = self.points[::-1]
            return True
        elif self.geom.type() == QGis.Polygon:
            points = self.setClockWiseRotation(self.geom.asPolygon()[0])
            yMax = self.geom.boundingBox().yMaximum()
            self.points = self.setFirstPointToNorth(points, yMax)
            return True            
        else:
            QMessageBox.information(self.iface.mainWindow(), self.tr("Warning!"), self.tr("The selected geometry should be a Line or a Polygon."))
            return False
            
    def calculate(self):
        """Constructs a list with distances and azimuths.
        """
        self.perimeter = 0
        self.distancesAndAzimuths = list()
        for i in xrange(0,len(self.points)-1):
            before = self.points[i]
            after = self.points[i+1]
            distance = math.sqrt(before.sqrDist(after))
            azimuth = before.azimuth(after)
            if azimuth < 0:
                azimuth += 360
            self.distancesAndAzimuths.append((distance, azimuth))
            self.perimeter += distance
            
        return self.distancesAndAzimuths
            
    def fillTextEdit(self):
        """Makes the CSV.
        """
        distancesAndAzimuths = list()
        isValid = self.isValidType()
        if isValid:
            distancesAndAzimuths = self.calculate()
        try:
            convergence = float(self.lineEdit.text())
        except ValueError:
            QMessageBox.information(self.iface.mainWindow(), self.tr("Warning!"), self.tr("Please, insert the meridian convergence."))
            return 
            
        isClosed = False
        if self.points[0] == self.points[len(self.points) - 1]:
            isClosed = True
        
        self.tableWidget.setRowCount(len(distancesAndAzimuths))

        for i in xrange(0,len(distancesAndAzimuths)):            
            azimuth = self.dd2dms(distancesAndAzimuths[i][1])
            realAzimuth = self.dd2dms(distancesAndAzimuths[i][1] + convergence)
            
            itemVertex = QTableWidgetItem("Pt"+str(i))
            self.tableWidget.setItem(i,0,itemVertex)
            itemE = QTableWidgetItem(str(self.points[i].x()))
            self.tableWidget.setItem(i,1,itemE)
            itemN = QTableWidgetItem(str(self.points[i].y()))            
            self.tableWidget.setItem(i,2,itemN)

            if (i == len(distancesAndAzimuths) - 1) and isClosed:
                itemSide = QTableWidgetItem("Pt"+str(i)+"-Pt0")
                self.tableWidget.setItem(i,3,itemSide)
            else:
                itemSide = QTableWidgetItem("Pt"+str(i)+"-Pt"+str(i+1))
                self.tableWidget.setItem(i,3,itemSide)

            itemAz = QTableWidgetItem(azimuth)
            self.tableWidget.setItem(i,4,itemAz)
            itemRealAz = QTableWidgetItem(realAzimuth)
            self.tableWidget.setItem(i,5,itemRealAz)
            dist = "%0.2f"%(distancesAndAzimuths[i][0])            
            itemDistance = QTableWidgetItem(dist)
            self.tableWidget.setItem(i,6,itemDistance)
            itemConfronting = QTableWidgetItem("")
            self.tableWidget.setItem(i,7,itemConfronting)
        
    def clearTextEdit(self):
        self.textEdit.clear()
        
    def dd2dms(self, dd):
        d = int(dd)
        m = abs(int(60*(dd-int(dd))))
        s = abs((dd-d-m/60)*60)
        dms = str(d) + u"\u00b0" + str(m).zfill(2) + "'" + "%0.2f"%(s) + "''"
        return dms
        
