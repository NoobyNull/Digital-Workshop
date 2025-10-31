# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'viewer_widget_vtk.ui'
##
## Created by: Qt User Interface Compiler version 6.6.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_Viewer3DWidget(object):
    def setupUi(self, Viewer3DWidget):
        if not Viewer3DWidget.objectName():
            Viewer3DWidget.setObjectName(u"Viewer3DWidget")
        Viewer3DWidget.resize(400, 300)
        Viewer3DWidget.setMinimumSize(QSize(400, 300))
        self.verticalLayout = QVBoxLayout(Viewer3DWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.vtk_container = QWidget(Viewer3DWidget)
        self.vtk_container.setObjectName(u"vtk_container")
        self.vtk_layout = QVBoxLayout(self.vtk_container)
        self.vtk_layout.setSpacing(0)
        self.vtk_layout.setObjectName(u"vtk_layout")
        self.vtk_layout.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout.addWidget(self.vtk_container)

        self.control_panel = QWidget(Viewer3DWidget)
        self.control_panel.setObjectName(u"control_panel")
        self.control_layout = QHBoxLayout(self.control_panel)
        self.control_layout.setObjectName(u"control_layout")
        self.control_layout.setContentsMargins(5, 5, 5, 5)
        self.solid_button = QPushButton(self.control_panel)
        self.solid_button.setObjectName(u"solid_button")
        self.solid_button.setCheckable(True)
        self.solid_button.setChecked(True)

        self.control_layout.addWidget(self.solid_button)

        self.wireframe_button = QPushButton(self.control_panel)
        self.wireframe_button.setObjectName(u"wireframe_button")
        self.wireframe_button.setCheckable(True)

        self.control_layout.addWidget(self.wireframe_button)

        self.points_button = QPushButton(self.control_panel)
        self.points_button.setObjectName(u"points_button")
        self.points_button.setCheckable(True)

        self.control_layout.addWidget(self.points_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.control_layout.addItem(self.horizontalSpacer)

        self.reset_button = QPushButton(self.control_panel)
        self.reset_button.setObjectName(u"reset_button")

        self.control_layout.addWidget(self.reset_button)


        self.verticalLayout.addWidget(self.control_panel)

        self.progress_frame = QWidget(Viewer3DWidget)
        self.progress_frame.setObjectName(u"progress_frame")
        self.progress_frame.setVisible(False)
        self.progress_layout = QHBoxLayout(self.progress_frame)
        self.progress_layout.setObjectName(u"progress_layout")
        self.progress_layout.setContentsMargins(5, 5, 5, 5)
        self.progress_label = QLabel(self.progress_frame)
        self.progress_label.setObjectName(u"progress_label")

        self.progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar(self.progress_frame)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setVisible(False)

        self.progress_layout.addWidget(self.progress_bar)

        self.progressSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.progress_layout.addItem(self.progressSpacer)


        self.verticalLayout.addWidget(self.progress_frame)


        self.retranslateUi(Viewer3DWidget)

        QMetaObject.connectSlotsByName(Viewer3DWidget)
    # setupUi

    def retranslateUi(self, Viewer3DWidget):
        Viewer3DWidget.setWindowTitle(QCoreApplication.translate("Viewer3DWidget", u"VTK 3D Model Viewer", None))
        self.solid_button.setText(QCoreApplication.translate("Viewer3DWidget", u"Solid", None))
        self.wireframe_button.setText(QCoreApplication.translate("Viewer3DWidget", u"Wireframe", None))
        self.points_button.setText(QCoreApplication.translate("Viewer3DWidget", u"Points", None))
        self.reset_button.setText(QCoreApplication.translate("Viewer3DWidget", u"Reset View", None))
        self.progress_label.setText(QCoreApplication.translate("Viewer3DWidget", u"Loading...", None))
    # retranslateUi

