# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'viewer_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.6.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (
    QCoreApplication,
    QMetaObject,
    QSize,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class Ui_Viewer3DWidget(object):
    def setupUi(self, Viewer3DWidget):
        if not Viewer3DWidget.objectName():
            Viewer3DWidget.setObjectName("Viewer3DWidget")
        Viewer3DWidget.resize(400, 300)
        Viewer3DWidget.setMinimumSize(QSize(400, 300))
        self.verticalLayout = QVBoxLayout(Viewer3DWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.viewer_container = QWidget(Viewer3DWidget)
        self.viewer_container.setObjectName("viewer_container")
        self.viewer_layout = QVBoxLayout(self.viewer_container)
        self.viewer_layout.setSpacing(0)
        self.viewer_layout.setObjectName("viewer_layout")
        self.viewer_layout.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout.addWidget(self.viewer_container)

        self.control_panel = QWidget(Viewer3DWidget)
        self.control_panel.setObjectName("control_panel")
        self.control_layout = QHBoxLayout(self.control_panel)
        self.control_layout.setObjectName("control_layout")
        self.control_layout.setContentsMargins(5, 5, 5, 5)
        self.solid_button = QPushButton(self.control_panel)
        self.solid_button.setObjectName("solid_button")
        self.solid_button.setCheckable(True)
        self.solid_button.setChecked(True)

        self.control_layout.addWidget(self.solid_button)

        self.wireframe_button = QPushButton(self.control_panel)
        self.wireframe_button.setObjectName("wireframe_button")
        self.wireframe_button.setCheckable(True)

        self.control_layout.addWidget(self.wireframe_button)

        self.points_button = QPushButton(self.control_panel)
        self.points_button.setObjectName("points_button")
        self.points_button.setCheckable(True)

        self.control_layout.addWidget(self.points_button)

        self.horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.control_layout.addItem(self.horizontalSpacer)

        self.reset_button = QPushButton(self.control_panel)
        self.reset_button.setObjectName("reset_button")

        self.control_layout.addWidget(self.reset_button)

        self.verticalLayout.addWidget(self.control_panel)

        self.progress_frame = QWidget(Viewer3DWidget)
        self.progress_frame.setObjectName("progress_frame")
        self.progress_frame.setVisible(False)
        self.progress_layout = QHBoxLayout(self.progress_frame)
        self.progress_layout.setObjectName("progress_layout")
        self.progress_layout.setContentsMargins(5, 5, 5, 5)
        self.progress_label = QLabel(self.progress_frame)
        self.progress_label.setObjectName("progress_label")

        self.progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar(self.progress_frame)
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setVisible(False)

        self.progress_layout.addWidget(self.progress_bar)

        self.progressSpacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.progress_layout.addItem(self.progressSpacer)

        self.verticalLayout.addWidget(self.progress_frame)

        self.retranslateUi(Viewer3DWidget)

        QMetaObject.connectSlotsByName(Viewer3DWidget)

    # setupUi

    def retranslateUi(self, Viewer3DWidget):
        Viewer3DWidget.setWindowTitle(
            QCoreApplication.translate("Viewer3DWidget", "3D Model Viewer", None)
        )
        self.solid_button.setText(
            QCoreApplication.translate("Viewer3DWidget", "Solid", None)
        )
        self.wireframe_button.setText(
            QCoreApplication.translate("Viewer3DWidget", "Wireframe", None)
        )
        self.points_button.setText(
            QCoreApplication.translate("Viewer3DWidget", "Points", None)
        )
        self.reset_button.setText(
            QCoreApplication.translate("Viewer3DWidget", "Reset View", None)
        )
        self.progress_label.setText(
            QCoreApplication.translate("Viewer3DWidget", "Loading...", None)
        )

    # retranslateUi
