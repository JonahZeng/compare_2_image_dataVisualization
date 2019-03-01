# _*_ encoding=utf-8 _*_
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPainter, QColor, QPen, QMouseEvent
from PyQt5.QtCore import QLineF, QPointF, QRectF, Qt, pyqtSignal

class ImageLabel(QLabel):
    inform_real_Pos = pyqtSignal(QPointF, QPointF)
    def __init__(self, color, penwidth, paintType, text='', parent=None):
        super().__init__(text, parent)
        self.flushPaintPosEdit = pyqtSignal()
        self.paintType = paintType
        self.penColor = color
        self.penWidth = penwidth
        self.paintCoordinates = [QPointF(0, 0), QPointF(0, 0)]
        self.startPt = None# type:QPointF
        self.paintBegin = False
        self.paintEnd = False
        
    def paintEvent(self, event):
        super().paintEvent(event)        
        if self.pixmap()==None:
            return
        if self.paintType == 'line' and (self.paintBegin or self.paintEnd):
            painter = QPainter(self)
            pen = QPen(self.penColor)
            pen.setWidth(self.penWidth)
            painter.setPen(pen)
            painter.drawLine(QLineF(self.paintCoordinates[0], self.paintCoordinates[1]))
        if self.paintType == 'rect' and (self.paintBegin or self.paintEnd):
            painter = QPainter(self)
            pen = QPen(self.penColor)
            pen.setWidth(self.penWidth)
            painter.setPen(pen)
            painter.drawRect(QRectF(self.paintCoordinates[0], self.paintCoordinates[1]))
                
    def setPaintType_Line(self):
        self.paintType = 'line'
        self.repaint()
        
    def setPaintType_Rect(self):
        self.paintType = 'rect'
        self.repaint()
    
    def setPenWidth(self, width:str):
        self.penWidth = int(width)
        self.repaint()
    
    def setPaintPenColor(self, color:QColor):
        self.penColor = color
        self.repaint()
    
    def mousePressEvent(self, event:QMouseEvent):
        if event.button()==Qt.LeftButton and self.paintBegin==False:
            self.paintBegin = True
            self.paintEnd = False
            self.paintCoordinates[0] = event.pos()
            self.inform_real_Pos.emit(self.paintCoordinates[0], self.paintCoordinates[1])
    
    def mouseReleaseEvent(self, event:QMouseEvent):
        if event.button()==Qt.LeftButton and self.paintBegin==True:
            self.paintBegin = False
            self.paintEnd = True
            self.paintCoordinates[1] = event.pos()
            self.inform_real_Pos.emit(self.paintCoordinates[0], self.paintCoordinates[1])
            
    def mouseMoveEvent(self, event:QMouseEvent):
        if self.paintBegin==True:
            self.paintCoordinates[1] = event.pos()
            self.inform_real_Pos.emit(self.paintCoordinates[0], self.paintCoordinates[1])
            self.repaint()
