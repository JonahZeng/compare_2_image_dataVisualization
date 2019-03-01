# _*_ encoding=utf-8 _*_

from PyQt5.QtWidgets import QDialog,  QPushButton,  QHBoxLayout,  QVBoxLayout,  QFrame,  QLabel

class aboutDlg(QDialog):
    def __init__(self,  parent):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        vlayout = QVBoxLayout()
        label = QLabel('<p>developer: z00438418/zengyangqiao@huawei.com</p> \
        <p><b>raw image data visualization</b></p>')
        hline = QFrame(self)
        hline.setFrameShape(QFrame.HLine)
        hline.setFrameShadow(QFrame.Sunken)
        vlayout.addWidget(label)
        vlayout.addWidget(hline)
        
        hlayout = QHBoxLayout()
        hlayout.addStretch(2)
        ok_btn = QPushButton('OK')
        hlayout.addWidget(ok_btn)
        
        vlayout.addLayout(hlayout)
        self.setLayout(vlayout)
        ok_btn.clicked.connect(self.accept)
        self.setWindowTitle('about this app')
        self.resize(200,  150)
