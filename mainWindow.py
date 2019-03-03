# _*_ encoding=utf-8 _*_
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QAction, QLabel, QScrollArea, QFileDialog, QDockWidget, \
    QGridLayout, QVBoxLayout, QHBoxLayout, QWidget, QButtonGroup, QRadioButton, QPushButton, QColorDialog, QComboBox, QLineEdit, QFrame, \
    QMenu
from PyQt5.QtGui import QFont, QImage, QImageReader, QPixmap, QKeySequence, QColor, QDragEnterEvent, QDropEvent, QDoubleValidator, QIntValidator
from PyQt5.QtCore import Qt, QDir, QStandardPaths, QSize, QPointF, QObject, QEvent
from aboutDlg import aboutDlg
from ImageLabel import ImageLabel
import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt
from matplotlib import cm
import math

class JonahWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAcceptDrops(True)#mainwindow是否接收拖动
        pathList = QStandardPaths.standardLocations(QStandardPaths.PicturesLocation)# type:tuple(list,str)
        self.workPath = pathList[-1] if len(pathList)>0 else QDir.currentPath()
        self.zoomIdx = 3
        self.zoomList = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]
        self.originSize = QSize(0, 0)
        self.originSize1 = QSize(0, 0)
        self.penColor = QColor(0, 170, 255)#初始化颜色
        self.opendFile = ''
        self.opendFile1 = ''
        self.initUI()
        screenInfo = QApplication.desktop()
        screenIdx = screenInfo.screenNumber()#current screen index
        screenRect = screenInfo.screenGeometry(screenIdx)
        self.setGeometry((screenRect.width()-1280)/2, (screenRect.height()-720)/2, 1280, 720)
        self.__setTitle()
        
    def initUI(self):
        fileMenu = self.menuBar().addMenu('&File')
        openFilesAction = QAction('Open files', self)
        exitAction = QAction('Exit', self)
        closeAction = QAction('Close', self)
        fileMenu.addAction(openFilesAction)
        fileMenu.addAction(closeAction)
        fileMenu.addAction(exitAction)
        openFilesAction.triggered.connect(self.onOpenFile)
        closeAction.triggered.connect(self.onCloseAction)
        exitAction.triggered.connect(self.onQuit)
        
        zoomMenu = self.menuBar().addMenu('&Zoom')
        zoomInAction = QAction('zoom in', self)
        zoomOutAction = QAction('zoom out', self)
        zoomMenu.addAction(zoomInAction)
        zoomMenu.addAction(zoomOutAction)
        zoomInAction.triggered.connect(self.zoomIn)
        zoomOutAction.triggered.connect(self.zoomOut)
        zoomInAction.setShortcut(QKeySequence(QKeySequence.ZoomIn))
        zoomOutAction.setShortcut(QKeySequence(QKeySequence.ZoomOut))
        
        viewMenu = self.menuBar().addMenu('&View')
        dockWidgetMenu = QMenu('dock widget', self)
        viewMenu.addMenu(dockWidgetMenu)
        self.penBoxAction = QAction('pen box', self)
        self.colorGamutAction = QAction('color gamut', self)
        dockWidgetMenu.addAction(self.penBoxAction)
        self.penBoxAction.setCheckable(True)
        self.penBoxAction.setChecked(True)
        dockWidgetMenu.addAction(self.colorGamutAction)
        self.colorGamutAction.setCheckable(True)
        self.colorGamutAction.setChecked(True)
                
        aboutMenu = self.menuBar().addMenu('&About')
        aboutQtAction = QAction('About Qt', self)
        aboutQtAction.triggered.connect(self.aboutQt_)
        aboutThisAction = QAction('About this', self)
        aboutThisAction.triggered.connect(self.aboutThis)
        aboutMenu.addAction(aboutQtAction)
        aboutMenu.addAction(aboutThisAction)
        
        self.mainWidget = QFrame()
        self.mainWidget.setFrameStyle(QFrame.Box|QFrame.Sunken)
        scrollAreaLayout = QHBoxLayout()
        self.mainWidget.setLayout(scrollAreaLayout)
        
        self.scrollArea = QScrollArea()
        self.imageLabel = ImageLabel(self.penColor, 2, 'rect')
        self.imageLabel.setText('drag image file to here!')
        self.imageLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.imageLabel.setScaledContents(True)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        
        self.scrollArea1 = QScrollArea()
        self.imageLabel1 = ImageLabel(self.penColor, 2, 'rect')
        self.imageLabel1.setText('drag image file to here!')
        self.imageLabel1.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.imageLabel1.setScaledContents(True)
        self.scrollArea1.setWidget(self.imageLabel1)
        self.scrollArea1.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        
        scrollAreaLayout.addWidget(self.scrollArea)
        scrollAreaLayout.addWidget(self.scrollArea1)
        
        self.setCentralWidget(self.mainWidget)
        
        
        self.createDockWidget()
        
        self.paintType_line_btn.toggled.connect(self.__setPaintType_line)
        self.paintType_rect_btn.toggled.connect(self.__setPaintType_rect)
        self.lineWidth_box.currentIndexChanged[str].connect(self.__setPenWidth)
        self.colorBtn.clicked.connect(self.__selectColor)
        self.paintOk.clicked.connect(self.__handleInputPaintPos)
        self.paintOk1.clicked.connect(self.__handleInputPaintPos1)
        self.syncRight.clicked.connect(self.__syncRightPos)
        self.syncLeft.clicked.connect(self.__syncLeftPos)
        
        self.createDockWidget_1()
        self.toolBoxWidget.installEventFilter(self)#拦截消息，关闭dock widget实际是隐藏
        self.plotDockWgt.installEventFilter(self)
        
        self.plot_rgb_contourf_line.clicked.connect(self.plot_rgb_contourf_line_func)
        self.plot_rgb_hist.clicked.connect(self.plot_rgb_hist_func)
        self.imageLabel.inform_real_Pos.connect(self.__flushPaintPosEdit)
        self.imageLabel1.inform_real_Pos.connect(self.__flushPaintPosEdit1)
        self.scrollArea.horizontalScrollBar().valueChanged.connect(self.__syncScrollArea1_horScBarVal)
        self.scrollArea.verticalScrollBar().valueChanged.connect(self.__syncScrollArea1_verScBarVal)
        self.scrollArea1.horizontalScrollBar().valueChanged.connect(self.__syncScrollArea_horScBarVal)
        self.scrollArea1.verticalScrollBar().valueChanged.connect(self.__syncScrollArea_verScBarVal)
        
        self.penBoxAction.toggled.connect(self.__toggleToolBoxDockWgt)
        self.colorGamutAction.toggled.connect(self.__toggleColorGamutWgt)
    
    def __syncScrollArea1_horScBarVal(self, value:int):
        '''
        同步两个图像区域的滚动条位置
        '''
        if not self.scrollArea.horizontalScrollBar().isVisible():
            return
        if not self.scrollArea1.horizontalScrollBar().isVisible():
            return
        try:
            pos_ratio = value/self.scrollArea.horizontalScrollBar().maximum()
            target_val = int(pos_ratio*self.scrollArea1.horizontalScrollBar().maximum()+0.5)
            self.scrollArea1.horizontalScrollBar().setValue(target_val)
        except ZeroDivisionError:
            return
            
    
    def __syncScrollArea1_verScBarVal(self, value:int):
        '''
        同步两个图像区域的滚动条位置
        '''
        if not self.scrollArea.verticalScrollBar().isVisible():
            return
        if not self.scrollArea1.verticalScrollBar().isVisible():
            return
        try:
            pos_ratio = value/self.scrollArea.verticalScrollBar().maximum()
            target_val = int(pos_ratio*self.scrollArea1.verticalScrollBar().maximum()+0.5)
            self.scrollArea1.verticalScrollBar().setValue(target_val)
        except ZeroDivisionError:
            return
    
    def __syncScrollArea_horScBarVal(self, value:int):
        '''
        同步两个图像区域的滚动条位置
        '''
        if not self.scrollArea.horizontalScrollBar().isVisible():
            return
        if not self.scrollArea1.horizontalScrollBar().isVisible():
            return
        try:
            pos_ratio = value/self.scrollArea1.horizontalScrollBar().maximum()
            target_val = int(pos_ratio*self.scrollArea.horizontalScrollBar().maximum()+0.5)
            self.scrollArea.horizontalScrollBar().setValue(target_val)
        except ZeroDivisionError:
            return
        
    def __syncScrollArea_verScBarVal(self, value:int):
        '''
        同步两个图像区域的滚动条位置
        '''
        if not self.scrollArea.verticalScrollBar().isVisible():
            return
        if not self.scrollArea1.verticalScrollBar().isVisible():
            return
        try:
            pos_ratio = value/self.scrollArea1.verticalScrollBar().maximum()
            target_val = int(pos_ratio*self.scrollArea.verticalScrollBar().maximum()+0.5)
            self.scrollArea.verticalScrollBar().setValue(target_val)
        except ZeroDivisionError:
            return
    
    def __setPaintType_line(self):
        '''
        设置绘图类型为直线
        '''
        self.imageLabel.setPaintType_Line()
        self.imageLabel1.setPaintType_Line()
    
    def __setPaintType_rect(self):
        '''
        设置绘图类型为矩形
        '''
        self.imageLabel.setPaintType_Rect()
        self.imageLabel1.setPaintType_Rect()
        
    def __setPenWidth(self, width:str):
        '''
        设置绘图线宽
        '''
        self.imageLabel.setPenWidth(width)
        self.imageLabel1.setPenWidth(width)
        
    def __toggleToolBoxDockWgt(self, checked:bool):
        '''
        菜单切换dock widget显示
        '''
        if checked:
            self.toolBoxWidget.show()
        else:
            self.toolBoxWidget.close()
    
    def __toggleColorGamutWgt(self, checked:bool):
        '''
        菜单切换dock widget显示
        '''
        if checked:
            self.plotDockWgt.show()
        else:
            self.plotDockWgt.close()
            
    def __syncRightPos(self):
        '''
        当点击面板上的sync按钮后，同步左右两侧的绘图坐标
        '''
        self.start_x_edit1.setText(self.start_x_edit.text())
        self.start_y_edit1.setText(self.start_y_edit.text())
        self.end_x_edit1.setText(self.end_x_edit.text())
        self.end_y_edit1.setText(self.end_y_edit.text())
        
    def __syncLeftPos(self):
        '''
        当点击面板上的sync按钮后，同步左右两侧的绘图坐标
        '''
        self.start_x_edit.setText(self.start_x_edit1.text())
        self.start_y_edit.setText(self.start_y_edit1.text())
        self.end_x_edit.setText(self.end_x_edit1.text())
        self.end_y_edit.setText(self.end_y_edit1.text())
    
    def createDockWidget(self):
        '''
        创建面板---绘图工具箱
        '''
        self.toolBoxWidget = QDockWidget(self)
        self.toolBoxWidget.setWindowTitle('pen box')
        self.toolBoxWidget.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        toolBoxContainer = QWidget()
        vlayout = QVBoxLayout()
        toolBoxContainer.setLayout(vlayout)
        self.toolBoxWidget.setWidget(toolBoxContainer)
        
        penGroup = QButtonGroup()
        penLayout = QHBoxLayout()
        self.paintType_line_btn = QRadioButton('line')
        self.paintType_rect_btn = QRadioButton('rect')
        self.paintType_rect_btn.setChecked(True)#初始形状 矩形
        penGroup.addButton(self.paintType_line_btn)
        penGroup.addButton(self.paintType_rect_btn)
        penLayout.addWidget(self.paintType_line_btn, 1)
        penLayout.addWidget(self.paintType_rect_btn, 1)
        penLayout.addStretch(1)
        
        lineWidth_layout = QHBoxLayout()
        lineWidth_text = QLabel('line width:')
        self.lineWidth_box = QComboBox()
        self.lineWidth_box.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '12', '14', '16', '18', '20', '24', '28', '32'])
        self.lineWidth_box.setCurrentIndex(1)
        lineWidth_layout.addWidget(lineWidth_text, 1)
        lineWidth_layout.addWidget(self.lineWidth_box, 1)
        lineWidth_layout.addStretch(1)
        
        colorLayout = QHBoxLayout()
        colorText = QLabel('color:')
        self.colorBtn = QPushButton('')
        colorLayout.addWidget(colorText, 1)
        colorLayout.addWidget(self.colorBtn, 1)
        colorLayout.addStretch(1)
        
        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        
        imageSizeValidator = QIntValidator(0, 10000)
        paintPosLayout0 = QGridLayout()
        start_x_text = QLabel('start x:')
        self.start_x_edit = QLineEdit()
        self.start_x_edit.setMaximumWidth(55)
        self.start_x_edit.setValidator(imageSizeValidator)
        start_y_text = QLabel('y:')
        self.start_y_edit = QLineEdit()
        self.start_y_edit.setMaximumWidth(55)
        self.start_y_edit.setValidator(imageSizeValidator)
        paintPosLayout0.addWidget(start_x_text, 0, 0, 1, 1)
        paintPosLayout0.addWidget(self.start_x_edit, 0, 1, 1, 1)
        paintPosLayout0.addWidget(start_y_text, 1, 0, 1, 1)
        paintPosLayout0.addWidget(self.start_y_edit, 1, 1, 1, 1)
        
        end_x_text = QLabel('end x:')
        self.end_x_edit = QLineEdit()
        self.end_x_edit.setMaximumWidth(55)
        self.end_x_edit.setValidator(imageSizeValidator)
        end_y_text = QLabel('y:')
        self.end_y_edit = QLineEdit()
        self.end_y_edit.setMaximumWidth(55)
        self.end_y_edit.setValidator(imageSizeValidator)
        paintPosLayout0.addWidget(end_x_text, 2, 0, 1, 1)
        paintPosLayout0.addWidget(self.end_x_edit, 2, 1, 1, 1)
        paintPosLayout0.addWidget(end_y_text, 3, 0, 1, 1)
        paintPosLayout0.addWidget(self.end_y_edit, 3, 1, 1, 1)
        
        self.paintOk = QPushButton('ok')
        self.paintOk.setStyleSheet('QPushButton{background:rgb(100,100,100); color:rgb(255,255,255)}')
        paintPosLayout0.addWidget(self.paintOk, 4, 1, 1, 1)
        
        vline1 = QFrame()
        vline1.setFrameShape(QFrame.VLine)
        syncLayout = QVBoxLayout()
        self.syncRight = QPushButton('--->')
        self.syncRight.setStyleSheet('QPushButton{background:rgb(100,100,100); color:rgb(30,30,192)}')
        self.syncLeft = QPushButton('<---')
        self.syncLeft.setStyleSheet('QPushButton{background:rgb(100,100,100); color:rgb(30,30,192)}')
        syncLayout.addWidget(self.syncRight)
        syncLayout.addWidget(self.syncLeft)
        vline2 = QFrame()
        vline2.setFrameShape(QFrame.VLine)
        
        paintPosLayout1 = QGridLayout()
        start_x_text1 = QLabel('start x:')
        self.start_x_edit1 = QLineEdit()
        self.start_x_edit1.setMaximumWidth(55)
        self.start_x_edit1.setValidator(imageSizeValidator)
        start_y_text1 = QLabel('y:')
        self.start_y_edit1 = QLineEdit()
        self.start_y_edit1.setMaximumWidth(55)
        self.start_y_edit1.setValidator(imageSizeValidator)
        paintPosLayout1.addWidget(start_x_text1, 0, 0, 1, 1)
        paintPosLayout1.addWidget(self.start_x_edit1, 0, 1, 1, 1)
        paintPosLayout1.addWidget(start_y_text1, 1, 0, 1, 1)
        paintPosLayout1.addWidget(self.start_y_edit1, 1, 1, 1, 1)
        end_x_text1 = QLabel('end x:')
        self.end_x_edit1 = QLineEdit()
        self.end_x_edit1.setMaximumWidth(55)
        self.end_x_edit1.setValidator(imageSizeValidator)
        end_y_text1 = QLabel('y:')
        self.end_y_edit1 = QLineEdit()
        self.end_y_edit1.setMaximumWidth(55)
        self.end_y_edit1.setValidator(imageSizeValidator)
        paintPosLayout1.addWidget(end_x_text1, 2, 0, 1, 1)
        paintPosLayout1.addWidget(self.end_x_edit1, 2, 1, 1, 1)
        paintPosLayout1.addWidget(end_y_text1, 3, 0, 1, 1)
        paintPosLayout1.addWidget(self.end_y_edit1, 3, 1, 1, 1)
        
        self.paintOk1 = QPushButton('ok')
        self.paintOk1.setStyleSheet('QPushButton{background:rgb(100,100,100); color:rgb(255,255,255)}')
        paintPosLayout1.addWidget(self.paintOk1, 4, 1, 1, 1)
        
        paintPosLayout = QHBoxLayout()
        paintPosLayout.addLayout(paintPosLayout0)
        paintPosLayout.addWidget(vline1)
        paintPosLayout.addLayout(syncLayout)
        paintPosLayout.addWidget(vline2)
        paintPosLayout.addLayout(paintPosLayout1)
        
        vlayout.addLayout(penLayout)
        vlayout.addLayout(lineWidth_layout)
        vlayout.addLayout(colorLayout)
        vlayout.addWidget(hline)
        vlayout.addLayout(paintPosLayout)
        vlayout.addStretch(1)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.toolBoxWidget)
        
        self.__setPenBtnColor()
        
    def __flushPaintPosEdit(self, startPt:QPointF, endPt:QPointF):
        '''
        接收的坐标是imagelabel的绘图坐标，需要根据当前的zoom计算出真实的图片坐标，并显示在面板上
        '''
        realStartPt = (startPt/self.zoomList[self.zoomIdx]).toPoint()
        realEndPt = (endPt/self.zoomList[self.zoomIdx]).toPoint()
        self.start_x_edit.setText(str(realStartPt.x()))
        self.start_y_edit.setText(str(realStartPt.y()))
        self.end_x_edit.setText(str(realEndPt.x()))
        self.end_y_edit.setText(str(realEndPt.y()))
        
    def __flushPaintPosEdit1(self, startPt:QPointF, endPt:QPointF):
        '''
        接收的坐标是imagelabel的绘图坐标，需要根据当前的zoom计算出真实的图片坐标
        '''
        realStartPt = (startPt/self.zoomList[self.zoomIdx]).toPoint()
        realEndPt = (endPt/self.zoomList[self.zoomIdx]).toPoint()
        self.start_x_edit1.setText(str(realStartPt.x()))
        self.start_y_edit1.setText(str(realStartPt.y()))
        self.end_x_edit1.setText(str(realEndPt.x()))
        self.end_y_edit1.setText(str(realEndPt.y()))
    
    def __handleInputPaintPos(self):
        try:
            if self.imageLabel.pixmap()==None:
                return
            else:
                maxWidth = self.imageLabel.pixmap().width()
                maxHeight = self.imageLabel.pixmap().height()
                start_x = int(self.start_x_edit.text())
                start_x = maxWidth if start_x>=maxWidth else start_x
                start_y = int(self.start_y_edit.text())
                start_y = maxHeight if start_y>=maxHeight else start_y
                end_x = int(self.end_x_edit.text())
                end_x = maxWidth if end_x>=maxWidth else end_x
                end_y = int(self.end_y_edit.text())
                end_y = maxHeight if end_y>=maxHeight else end_y
                
                scale_ratio = self.zoomList[self.zoomIdx]
                self.imageLabel.paintCoordinates[0] = QPointF(float(start_x)*scale_ratio, float(start_y)*scale_ratio)
                self.imageLabel.paintCoordinates[1] = QPointF(float(end_x)*scale_ratio, float(end_y)*scale_ratio)
                self.imageLabel.paintEnd = True
                self.imageLabel.repaint()
        except ValueError:
            pass
            
    def __handleInputPaintPos1(self):
        try:
            if self.imageLabel1.pixmap()==None:
                return
            else:
                maxWidth = self.imageLabel1.pixmap().width()
                maxHeight = self.imageLabel1.pixmap().height()
                start_x = int(self.start_x_edit.text())
                start_x = maxWidth if start_x>=maxWidth else start_x
                start_y = int(self.start_y_edit.text())
                start_y = maxHeight if start_y>=maxHeight else start_y
                end_x = int(self.end_x_edit.text())
                end_x = maxWidth if end_x>=maxWidth else end_x
                end_y = int(self.end_y_edit.text())
                end_y = maxHeight if end_y>=maxHeight else end_y
                
                scale_ratio = self.zoomList[self.zoomIdx]
                self.imageLabel1.paintCoordinates[0] = QPointF(float(start_x)*scale_ratio, float(start_y)*scale_ratio)
                self.imageLabel1.paintCoordinates[1] = QPointF(float(end_x)*scale_ratio, float(end_y)*scale_ratio)
                self.imageLabel1.paintEnd = True
                self.imageLabel1.repaint()
        except ValueError:
            pass
            
    def createDockWidget_1(self):
        '''
        创建绘图工具箱，包含绘图类型，线宽，颜色，坐标值
        '''
        self.plotDockWgt = QDockWidget(self)
        self.plotDockWgt.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.plotDockWgt.setWindowTitle('color gamut type')
        #self.plotDockWgt.setFeatures(QDockWidget.DockWidgetClosable|QDockWidget.DockWidgetMovable|QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetVerticalTitleBar)
        pltWgtContainer = QWidget()
        vlayout = QVBoxLayout()
        pltWgtContainer.setLayout(vlayout)
        self.plotDockWgt.setWidget(pltWgtContainer)
        
        plot_btn_layout = QGridLayout()
        self.plot_rgb_contourf_line = QPushButton('rgb contour/line')
        self.plot_rgb_hist = QPushButton('rgb hist')
        self.plot_yuv_contourf_line = QPushButton('yuv contour/line')
        self.plot_yuv_hist = QPushButton('yuv hist')
        self.plot_hsv_contourf_line = QPushButton('hsv contour/line')
        self.plot_hsv_hist = QPushButton('hsv hist')
        plot_btn_layout.addWidget(self.plot_rgb_contourf_line, 0, 0, 1, 1)
        plot_btn_layout.addWidget(self.plot_rgb_hist, 0, 1, 1, 1)
        plot_btn_layout.addWidget(self.plot_yuv_contourf_line, 1, 0, 1, 1)
        plot_btn_layout.addWidget(self.plot_yuv_hist, 1, 1, 1, 1)
        plot_btn_layout.addWidget(self.plot_hsv_contourf_line, 2, 0, 1, 1)
        plot_btn_layout.addWidget(self.plot_hsv_hist, 2, 1, 1, 1)
        
        vlayout.addLayout(plot_btn_layout)
        
        rgb2yuv_mat_layout = QGridLayout()
        rgb2yuv_mat_label = QLabel('rgb2yuv:')
        rgb2yuv_mat_layout.addWidget(rgb2yuv_mat_label, 0, 0, 1, 1)
        validtor = QDoubleValidator(-5.0, 5.0, 10)
        self.rgb2yuv_mat_0 = QLineEdit('0.299')
        self.rgb2yuv_mat_0.setMaximumWidth(55)
        self.rgb2yuv_mat_0.setValidator(validtor)
        self.rgb2yuv_mat_1 = QLineEdit('0.587')
        self.rgb2yuv_mat_1.setMaximumWidth(55)
        self.rgb2yuv_mat_1.setValidator(validtor)
        self.rgb2yuv_mat_2 = QLineEdit('0.114')
        self.rgb2yuv_mat_2.setMaximumWidth(55)
        self.rgb2yuv_mat_2.setValidator(validtor)
        self.rgb2yuv_mat_3 = QLineEdit('-0.147')
        self.rgb2yuv_mat_3.setMaximumWidth(55)
        self.rgb2yuv_mat_3.setValidator(validtor)
        self.rgb2yuv_mat_4 = QLineEdit('-0.289')
        self.rgb2yuv_mat_4.setMaximumWidth(55)
        self.rgb2yuv_mat_4.setValidator(validtor)
        self.rgb2yuv_mat_5 = QLineEdit('0.436')
        self.rgb2yuv_mat_5.setMaximumWidth(55)
        self.rgb2yuv_mat_5.setValidator(validtor)
        self.rgb2yuv_mat_6 = QLineEdit('0.615')
        self.rgb2yuv_mat_6.setMaximumWidth(55)
        self.rgb2yuv_mat_6.setValidator(validtor)
        self.rgb2yuv_mat_7 = QLineEdit('-0.515')
        self.rgb2yuv_mat_7.setMaximumWidth(55)
        self.rgb2yuv_mat_7.setValidator(validtor)
        self.rgb2yuv_mat_8 = QLineEdit('-0.100')
        self.rgb2yuv_mat_8.setMaximumWidth(55)
        self.rgb2yuv_mat_8.setValidator(validtor)
        rgb2yuv_mat_layout.addWidget(self.rgb2yuv_mat_0, 1, 0, 1, 1)
        rgb2yuv_mat_layout.addWidget(self.rgb2yuv_mat_1, 1, 1, 1, 1)
        rgb2yuv_mat_layout.addWidget(self.rgb2yuv_mat_2, 1, 2, 1, 1)
        rgb2yuv_mat_layout.addWidget(self.rgb2yuv_mat_3, 2, 0, 1, 1)
        rgb2yuv_mat_layout.addWidget(self.rgb2yuv_mat_4, 2, 1, 1, 1)
        rgb2yuv_mat_layout.addWidget(self.rgb2yuv_mat_5, 2, 2, 1, 1)
        rgb2yuv_mat_layout.addWidget(self.rgb2yuv_mat_6, 3, 0, 1, 1)
        rgb2yuv_mat_layout.addWidget(self.rgb2yuv_mat_7, 3, 1, 1, 1)
        rgb2yuv_mat_layout.addWidget(self.rgb2yuv_mat_8, 3, 2, 1, 1)
        rgb2yuv_mat_layout.setColumnMinimumWidth(0, 20)
        rgb2yuv_mat_layout.setColumnMinimumWidth(1, 20)
        rgb2yuv_mat_layout.setColumnMinimumWidth(2, 20)
        
        vlayout.addLayout(rgb2yuv_mat_layout)
        vlayout.addStretch(1)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.plotDockWgt)
    
    def plot_rgb_contourf_line_func(self):
        if self.imageLabel.paintEnd==False or self.imageLabel.pixmap()==None:
            return
        pos_0, pos_1 = QPointF(self.imageLabel.paintCoordinates[0])/self.zoomList[self.zoomIdx], QPointF(self.imageLabel.paintCoordinates[1])/self.zoomList[self.zoomIdx]
        x_0, x_1, y_0, y_1 = pos_0.x(), pos_1.x(), pos_0.y(), pos_1.y()
        if x_0==x_1 and y_0==y_1:
            return
        if self.paintType_rect_btn.isChecked():
            if x_0 > x_1:
                x_0, x_1 = x_1, x_0
            if y_0 > y_1:
                y_0, y_1 = y_1, y_0
            data = cv.imread(self.opendFile)
            if data is None:
                QMessageBox.information(self, 'information', 'can not open image', QMessageBox.Ok)
                return
            data_r = data[int(y_0):int(y_1), int(x_0):int(x_1), 2]
            data_g = data[int(y_0):int(y_1), int(x_0):int(x_1), 1]
            data_b = data[int(y_0):int(y_1), int(x_0):int(x_1), 0]
            data_max = np.max([data_r.max(), data_g.max(), data_b.max()])
            data_min = np.max([data_r.min(), data_g.min(), data_b.min()])
            X = np.arange(data_r.shape[1])
            Y = np.arange(data_r.shape[0])
            X, Y = np.meshgrid(X, Y)
            fig = plt.figure(0, figsize=(4, 9))
            ax1 = fig.add_subplot(311)
            surf1 = ax1.contourf(X, Y, data_r, np.linspace(data_min-5, data_max+5, 11), cmap=cm.get_cmap('coolwarm'))
            ax1.set_ylim([data_r.shape[0], 0])
            ax1.set_title('r contour')
            fig.colorbar(surf1)
        
            ax2 = fig.add_subplot(312)
            surf2 = ax2.contourf(X, Y, data_g, np.linspace(data_min-5, data_max+5, 11), cmap=cm.get_cmap('coolwarm'))
            ax2.set_ylim([data_g.shape[0], 0])
            ax2.set_title('g contour')
            fig.colorbar(surf2)
        
            ax3 = fig.add_subplot(313)
            surf3 = ax3.contourf(X, Y, data_b, np.linspace(data_min-5, data_max+5, 11), cmap=cm.get_cmap('coolwarm'))
            ax3.set_ylim([data_b.shape[0], 0])
            ax3.set_title('b contour')
            fig.colorbar(surf3)
            fig.tight_layout()
            plt.show()
        elif self.paintType_line_btn.isChecked():
            if x_0 > x_1:
                x_0, x_1 = x_1, x_0
                y_0, y_1 = y_1, y_0
            data = cv.imread(self.opendFile)
            if data is None:
                QMessageBox.information(self, 'information', 'can not open image', QMessageBox.Ok)
                return
            if x_0==x_1:
                if y_0<y_1:
                    data_r = data[y_0:y_1, x_0, 2]
                    data_g = data[y_0:y_1, x_0, 1]
                    data_b = data[y_0:y_1, x_0, 0]
                else:
                    data_r = data[y_0:y_1:-1, x_0, 2]
                    data_g = data[y_0:y_1:-1, x_0, 1]
                    data_b = data[y_0:y_1:-1, x_0, 0]
            elif y_0==y_1:
                data_r = data[y_0, x_0:x_1, 2]
                data_g = data[y_0, x_0:x_1, 1]
                data_b = data[y_0, x_0:x_1, 0]
            else:
                length = math.sqrt((x_1-x_0)*(x_1-x_0) + (y_1-y_0)*(y_1-y_0))
                data_r = np.zeros((int(length), ), np.uint8)
                data_g = np.zeros((int(length), ), np.uint8)
                data_b = np.zeros((int(length), ), np.uint8)
                k = (y_1-y_0)/(x_1-x_0)
                for l in range(int(length)):
                    delt_x = math.sqrt((l*l)/(1+k*k))
                    delt_y = k*delt_x
                    data_r[l] = data[int(y_0+delt_y+0.5), int(x_0+delt_x+0.5), 2]
                    data_g[l] = data[int(y_0+delt_y+0.5), int(x_0+delt_x+0.5), 1]
                    data_b[l] = data[int(y_0+delt_y+0.5), int(x_0+delt_x+0.5), 0]
                fig = plt.figure(0, figsize=(6, 4))
                ax = fig.add_subplot(111)
                ax.plot(data_r, 'r-', data_g, 'g-', data_b, 'b-')
                plt.show()
                    
                
    def eventFilter(self, obj:QObject, event:QEvent):
        if obj is self.toolBoxWidget and event.type()==QEvent.Close:
            #self.toolBoxWidget.hide()
            self.penBoxAction.setChecked(False)
            return True
        if obj is self.plotDockWgt and event.type()==QEvent.Close:
            #self.plotDockWgt.hide()
            self.colorGamutAction.setChecked(False)
            return True
        
        return super().eventFilter(obj, event)
            
    
    def plot_rgb_hist_func(self):
        if self.imageLabel.paintEnd==False or self.imageLabel.pixmap()==None:
            return
        pos_0, pos_1 = QPointF(self.imageLabel.paintCoordinates[0])/self.zoomList[self.zoomIdx], QPointF(self.imageLabel.paintCoordinates[1])/self.zoomList[self.zoomIdx]
        x_0, x_1, y_0, y_1 = pos_0.x(), pos_1.x(), pos_0.y(), pos_1.y()
        if self.paintType_rect_btn.isChecked():
            if x_0 > x_1:
                x_0, x_1 = x_1, x_0
            if y_0 > y_1:
                y_0, y_1 = y_1, y_0
        elif self.paintType_line_btn.isChecked():
            if x_0 > x_1:
                x_0, x_1 = x_1, x_0
                y_0, y_1 = y_1, y_0
        data = cv.imread(self.opendFile)
        if data is None:
            QMessageBox.information(self, 'information', 'can not open image', QMessageBox.Ok)
            return
        data_r = data[int(y_0):int(y_1), int(x_0):int(x_1), 2].flatten()
        data_g = data[int(y_0):int(y_1), int(x_0):int(x_1), 1].flatten()
        data_b = data[int(y_0):int(y_1), int(x_0):int(x_1), 0].flatten()
        n_bins = 64
        
        fig = plt.figure(0, figsize=(4, 6))
        ax1 = fig.add_subplot(311)
        N1, bins1, pathch1 = ax1.hist(data_r, n_bins, histtype='bar', color='r', label='R')
        ax1.set_title('r hist')
        
        ax2 = fig.add_subplot(312)
        N2, bins2, pathch2 = ax2.hist(data_g, n_bins, histtype='bar', color='g', label='G')
        ax2.set_title('g hist')
        
        ax3 = fig.add_subplot(313)
        N3, bins3, pathch3 = ax3.hist(data_b, n_bins, histtype='bar', color='b', label='B')
        ax3.set_title('b hist')
        N_max = np.max([N1.max(), N2.max(), N3.max()])
        ax1.set_ylim([0, N_max])
        ax1.set_xlim([0, 255])
        ax2.set_ylim([0, N_max])
        ax2.set_xlim([0, 255])
        ax3.set_ylim([0, N_max])
        ax3.set_xlim([0, 255])
        fig.tight_layout()
        plt.show()

        
    def __setPenBtnColor(self):        
        self.colorBtn.setStyleSheet('QPushButton{background:rgb(%d,%d,%d);border:none;}'%(self.penColor.red(), self.penColor.green(), self.penColor.blue()))

        
    def __selectColor(self):
        dlg = QColorDialog(self.penColor, self.toolBoxWidget)
        reply = dlg.exec_()
        if reply == QColorDialog.Accepted:
            self.penColor = dlg.selectedColor()
            self.__setPenBtnColor()
            self.imageLabel.setPaintPenColor(self.penColor)
            self.imageLabel1.setPaintPenColor(self.penColor)
        

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'question', 'are you sure to quit?', QMessageBox.Yes|QMessageBox.No)
        if reply == QMessageBox.Yes:
            super().closeEvent(event)
        else:
            event.ignore()
            
    def onQuit(self):
        self.close()
    
    def onCloseAction(self):
        if self.imageLabel.pixmap()==None and self.imageLabel1.pixmap()==None:
            return
        self.imageLabel.clear()
        self.imageLabel.setText('drag image file to here!')
        self.imageLabel.adjustSize()
        self.imageLabel.paintBegin = False
        self.imageLabel.paintEnd = False
        self.imageLabel1.clear()
        self.imageLabel1.setText('drag image file to here!')
        self.imageLabel1.adjustSize()
        self.imageLabel1.paintBegin = False
        self.imageLabel1.paintEnd = False
        self.opendFile = ''
        self.opendFile1 = ''
        self.__setTitle()
        self.start_x_edit.setText('')
        self.start_y_edit.setText('')
        self.end_x_edit.setText('')
        self.end_y_edit.setText('')
        self.start_x_edit1.setText('')
        self.start_y_edit1.setText('')
        self.end_x_edit1.setText('')
        self.end_y_edit1.setText('')
        
    def onOpenFile(self):
        fileList = QFileDialog.getOpenFileNames(self, 'open', self.workPath, 'Images(*.jpg *.jpeg *.png *.bmp);;All file(*.*)')# type:list[str]
        if len(fileList)<=0 or len(fileList[0])<=0:
            return
        reader = QImageReader(fileList[0][0])
        reader.setAutoTransform(True)
        img = reader.read()
        if img.isNull():
            QMessageBox.information(self, 'error', 'can not open %s as image!'%fileList[0][0], QMessageBox.Ok)
            return
        self.opendFile = fileList[0][0]
        self.__setImage(img, self.zoomList[self.zoomIdx])
        if len(fileList[0])>=2:
            reader1 =QImageReader(fileList[0][1])
            reader1.setAutoTransform(True)
            img1 = reader1.read()
            if img1.isNull():
                QMessageBox.information(self, 'error', 'can not open %s as image!'%fileList[0][0], QMessageBox.Ok)
                return
            self.__setImage1(img1, self.zoomList[self.zoomIdx])
            self.opendFile1 = fileList[0][1]
        self.__setTitle()
        
    def __setTitle(self):
        if self.opendFile=='' and self.opendFile1=='':
            self.setWindowTitle('raw_image_data_visual')
        elif self.opendFile=='' or self.opendFile1=='':
            self.setWindowTitle(self.opendFile + self.opendFile1)
        else:
            self.setWindowTitle(self.opendFile +'<--->'+ self.opendFile1)
        
    def __setImage(self, image:QImage, factor:float):
        pixMap = QPixmap.fromImage(image)
        self.originSize = pixMap.size()
        self.imageLabel.paintBegin = False
        self.imageLabel.paintEnd = False
        self.imageLabel.setPixmap(pixMap)
        self.__adjustImgLabelSize_scrollbarPos()
        
    def __setImage1(self, image:QImage, factor:float):
        pixMap = QPixmap.fromImage(image)
        self.originSize1 = pixMap.size()
        self.imageLabel1.paintBegin = False
        self.imageLabel1.paintEnd = False
        self.imageLabel1.setPixmap(pixMap)
        self.__adjustImgLabelSize_scrollbarPos1()
    
    def zoomIn(self):
        if self.imageLabel.pixmap() == None or self.originSize == QSize(0, 0):
            return
        if(self.zoomIdx < len(self.zoomList)-1):
            self.zoomIdx = self.zoomIdx + 1
        else:
            return
        scale_ratio = self.zoomList[self.zoomIdx]
        if self.imageLabel.paintEnd == True:
            self.imageLabel.paintCoordinates[0] = QPointF(float(self.start_x_edit.text())*scale_ratio, float(self.start_y_edit.text())*scale_ratio)
            self.imageLabel.paintCoordinates[1] = QPointF(float(self.end_x_edit.text())*scale_ratio, float(self.end_y_edit.text())*scale_ratio)
        self.__adjustImgLabelSize_scrollbarPos()#缩放image label
        if self.imageLabel1.paintEnd == True:
            self.imageLabel1.paintCoordinates[0] = QPointF(float(self.start_x_edit1.text())*scale_ratio, float(self.start_y_edit1.text())*scale_ratio)
            self.imageLabel1.paintCoordinates[1] = QPointF(float(self.end_x_edit1.text())*scale_ratio, float(self.end_y_edit1.text())*scale_ratio)
        self.__adjustImgLabelSize_scrollbarPos1()#因为已经关联了另一个scrollbar，会自动调整
            
    def zoomOut(self):
        if self.imageLabel.pixmap() == None or self.originSize == QSize(0, 0):
            return
        if self.zoomIdx > 0:
            self.zoomIdx = self.zoomIdx - 1
        else:
            return
        scale_ratio = self.zoomList[self.zoomIdx]/self.zoomList[self.zoomIdx+1]
        if self.imageLabel.paintEnd == True:
            self.imageLabel.paintCoordinates[0] = self.imageLabel.paintCoordinates[0]*scale_ratio
            self.imageLabel.paintCoordinates[1] = self.imageLabel.paintCoordinates[1]*scale_ratio
        self.__adjustImgLabelSize_scrollbarPos()
        if self.imageLabel1.paintEnd == True:
            self.imageLabel1.paintCoordinates[0] = self.imageLabel1.paintCoordinates[0]*scale_ratio
            self.imageLabel1.paintCoordinates[1] = self.imageLabel1.paintCoordinates[1]*scale_ratio #缩放绘图
        self.__adjustImgLabelSize_scrollbarPos1()#缩放image label

            
    def __adjustImgLabelSize_scrollbarPos(self):
        self.imageLabel.resize(self.originSize*self.zoomList[self.zoomIdx])
        if self.scrollArea.horizontalScrollBar().maximum() - self.scrollArea.horizontalScrollBar().minimum() > 0:
            self.scrollArea.horizontalScrollBar().setValue((self.scrollArea.horizontalScrollBar().maximum() - self.scrollArea.horizontalScrollBar().minimum())//2)
        if self.scrollArea.verticalScrollBar().maximum() - self.scrollArea.verticalScrollBar().minimum() > 0:
            self.scrollArea.verticalScrollBar().setValue((self.scrollArea.verticalScrollBar().maximum() - self.scrollArea.verticalScrollBar().minimum())//2)
            
    def __adjustImgLabelSize_scrollbarPos1(self):
        self.imageLabel1.resize(self.originSize1*self.zoomList[self.zoomIdx])
        if self.scrollArea1.horizontalScrollBar().maximum() - self.scrollArea1.horizontalScrollBar().minimum() > 0:
            self.scrollArea1.horizontalScrollBar().setValue((self.scrollArea1.horizontalScrollBar().maximum() - self.scrollArea1.horizontalScrollBar().minimum())//2)
        if self.scrollArea1.verticalScrollBar().maximum() - self.scrollArea1.verticalScrollBar().minimum() > 0:
            self.scrollArea1.verticalScrollBar().setValue((self.scrollArea1.verticalScrollBar().maximum() - self.scrollArea1.verticalScrollBar().minimum())//2)
            
    def dragEnterEvent(self, event:QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
        
    def dropEvent(self, event:QDropEvent):
        mainWidget_rect = self.mainWidget.geometry()
        dropPt = event.pos()
        if dropPt.x()<mainWidget_rect.left() or dropPt.x()>mainWidget_rect.right() or dropPt.y()<mainWidget_rect.top() or dropPt.y()>mainWidget_rect.bottom():
            return
        mData = event.mimeData()
        if not mData.hasUrls():
            return        
        urlList = mData.urls()
        if len(urlList)==1:
            scrollArea_rect = self.scrollArea.geometry().translated(mainWidget_rect.topLeft())
            scrollArea1_rect = self.scrollArea1.geometry().translated(mainWidget_rect.topLeft())
            if dropPt.x()>scrollArea_rect.left() and dropPt.x()<scrollArea_rect.right():
                fileName = urlList[0].toLocalFile()
                if len(fileName)<=0 or fileName==None:
                    return
                if fileName.endswith(('.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG', '.bmp', '.BMP')):
                    reader = QImageReader(fileName)
                    reader.setAutoTransform(True)
                    img = reader.read()
                    if img.isNull():
                        QMessageBox.information(self, 'error', 'can not open %s as image!'%fileName, QMessageBox.Ok)
                        return
                    self.opendFile = fileName
                    self.__setTitle()
                    self.__setImage(img, self.zoomList[self.zoomIdx])
            elif dropPt.x()>scrollArea1_rect.left() and dropPt.x()<scrollArea1_rect.right():
                fileName = urlList[0].toLocalFile()
                if len(fileName)<=0 or fileName==None:
                    return
                if fileName.endswith(('.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG', '.bmp', '.BMP')):
                    reader = QImageReader(fileName)
                    reader.setAutoTransform(True)
                    img = reader.read()
                    if img.isNull():
                        QMessageBox.information(self, 'error', 'can not open %s as image!'%fileName, QMessageBox.Ok)
                        return
                    self.opendFile1 = fileName
                    self.__setTitle()
                    self.__setImage1(img, self.zoomList[self.zoomIdx])
            else:
                pass
                    
        elif len(urlList)>=2:
            fileName = urlList[0].toLocalFile()
            fileName1 = urlList[1].toLocalFile()
            if len(fileName)<=0 or fileName==None or len(fileName1)<=0 or fileName1==None:
                return
            if fileName.endswith(('.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG', '.bmp', '.BMP')) and fileName1.endswith(('.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG', '.bmp', '.BMP')):
                reader = QImageReader(fileName)
                reader.setAutoTransform(True)
                img = reader.read()
                reader1 = QImageReader(fileName1)
                reader1.setAutoTransform(True)
                img1 = reader1.read()
                if img.isNull() or img1.isNull():
                    QMessageBox.information(self, 'error', 'can not open %s %sas image!'%(fileName, fileName1), QMessageBox.Ok)
                    return
                self.opendFile = fileName
                self.opendFile1 = fileName1
                self.__setTitle()
                self.__setImage(img, self.zoomList[self.zoomIdx])
                self.__setImage1(img1, self.zoomList[self.zoomIdx])
        else:
            pass
        
    def aboutQt_(self):
        QApplication.instance().aboutQt()
    
    def aboutThis(self):
        dlg = aboutDlg(self)
        dlg.exec_()
        
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei UI", 10))
    window = JonahWindow()
    window.show()
    sys.exit(app.exec_())
