# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.6.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QDockWidget, QLabel, QMainWindow,
    QMenu, QMenuBar, QProgressBar, QSizePolicy,
    QStatusBar, QTextEdit, QToolBar, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1600, 1000)
        MainWindow.setMinimumSize(QSize(1200, 800))
        MainWindow.setDockOptions(QMainWindow.AllowNestedDocks|QMainWindow.AllowTabbedDocks|QMainWindow.AnimatedDocks)
        MainWindow.setStyleSheet(u"QMainWindow {\n"
"    background-color: #ffffff;\n"
"    color: #000000;\n"
"}\n"
"QDockWidget {\n"
"    background-color: #ffffff;\n"
"    color: #000000;\n"
"    border: 1px solid #d0d0d0;\n"
"    font-weight: bold;\n"
"}\n"
"QDockWidget::title {\n"
"    background-color: #f5f5f5;\n"
"    padding: 5px;\n"
"    border-bottom: 1px solid #d0d0d0;\n"
"}\n"
"QToolBar {\n"
"    background-color: #f5f5f5;\n"
"    border: 1px solid #d0d0d0;\n"
"    spacing: 3px;\n"
"    color: #000000;\n"
"}\n"
"QMenuBar {\n"
"    background-color: #f5f5f5;\n"
"    color: #000000;\n"
"    border-bottom: 1px solid #d0d0d0;\n"
"}\n"
"QMenuBar::item {\n"
"    background-color: transparent;\n"
"    padding: 4px 8px;\n"
"}\n"
"QMenuBar::item:selected {\n"
"    background-color: #0078d4;\n"
"    color: #ffffff;\n"
"}\n"
"QStatusBar {\n"
"    background-color: #f5f5f5;\n"
"    color: #000000;\n"
"    border-top: 1px solid #d0d0d0;\n"
"}\n"
"QLabel {\n"
"    color: #000000;\n"
"}\n"
"QPushButton {\n"
"    background-color: #f5f5f5;\n"
"    "
                        "color: #000000;\n"
"    border: 1px solid #d0d0d0;\n"
"    padding: 4px 12px;\n"
"    border-radius: 2px;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: #e1e1e1;\n"
"}\n"
"QPushButton:pressed {\n"
"    background-color: #d0d0d0;\n"
"}")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName(u"actionOpen")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.actionPreferences = QAction(MainWindow)
        self.actionPreferences.setObjectName(u"actionPreferences")
        self.actionZoomIn = QAction(MainWindow)
        self.actionZoomIn.setObjectName(u"actionZoomIn")
        self.actionZoomOut = QAction(MainWindow)
        self.actionZoomOut.setObjectName(u"actionZoomOut")
        self.actionResetView = QAction(MainWindow)
        self.actionResetView.setObjectName(u"actionResetView")
        self.actionAbout = QAction(MainWindow)
        self.actionAbout.setObjectName(u"actionAbout")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.viewer_widget = QTextEdit(self.centralwidget)
        self.viewer_widget.setObjectName(u"viewer_widget")
        self.viewer_widget.setReadOnly(True)
        self.viewer_widget.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.viewer_widget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1600, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuEdit = QMenu(self.menubar)
        self.menuEdit.setObjectName(u"menuEdit")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName(u"menuView")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.MainToolBar = QToolBar(MainWindow)
        self.MainToolBar.setObjectName(u"MainToolBar")
        MainWindow.addToolBar(Qt.TopToolBarArea, self.MainToolBar)
        self.status_bar = QStatusBar(MainWindow)
        self.status_bar.setObjectName(u"status_bar")
        self.status_label = QLabel(self.status_bar)
        self.status_label.setObjectName(u"status_label")
        self.progress_bar = QProgressBar(self.status_bar)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setVisible(False)
        self.memory_label = QLabel(self.status_bar)
        self.memory_label.setObjectName(u"memory_label")
        MainWindow.setStatusBar(self.status_bar)
        self.model_library_dock = QDockWidget(MainWindow)
        self.model_library_dock.setObjectName(u"model_library_dock")
        self.model_library_dock.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.model_library_widget = QTextEdit()
        self.model_library_widget.setObjectName(u"model_library_widget")
        self.model_library_widget.setReadOnly(True)
        self.model_library_dock.setWidget(self.model_library_widget)
        MainWindow.addDockWidget(Qt.LeftDockWidgetArea, self.model_library_dock)
        self.properties_dock = QDockWidget(MainWindow)
        self.properties_dock.setObjectName(u"properties_dock")
        self.properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.properties_widget = QTextEdit()
        self.properties_widget.setObjectName(u"properties_widget")
        self.properties_widget.setReadOnly(True)
        self.properties_dock.setWidget(self.properties_widget)
        MainWindow.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
        self.metadata_dock = QDockWidget(MainWindow)
        self.metadata_dock.setObjectName(u"metadata_dock")
        self.metadata_dock.setAllowedAreas(Qt.BottomDockWidgetArea|Qt.TopDockWidgetArea)
        self.metadata_widget = QTextEdit()
        self.metadata_widget.setObjectName(u"metadata_widget")
        self.metadata_widget.setReadOnly(True)
        self.metadata_dock.setWidget(self.metadata_widget)
        MainWindow.addDockWidget(Qt.BottomDockWidgetArea, self.metadata_dock)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuEdit.addAction(self.actionPreferences)
        self.menuView.addAction(self.actionZoomIn)
        self.menuView.addAction(self.actionZoomOut)
        self.menuView.addSeparator()
        self.menuView.addAction(self.actionResetView)
        self.menuHelp.addAction(self.actionAbout)
        self.MainToolBar.addAction(self.actionOpen)
        self.MainToolBar.addSeparator()
        self.MainToolBar.addAction(self.actionZoomIn)
        self.MainToolBar.addAction(self.actionZoomOut)
        self.MainToolBar.addAction(self.actionResetView)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"3D-MM - 3D Model Manager", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", u"&Open Model...", None))
#if QT_CONFIG(shortcut)
        self.actionOpen.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(statustip)
        self.actionOpen.setStatusTip(QCoreApplication.translate("MainWindow", u"Open a 3D model file", None))
#endif // QT_CONFIG(statustip)
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"E&xit", None))
#if QT_CONFIG(shortcut)
        self.actionExit.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+Q", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(statustip)
        self.actionExit.setStatusTip(QCoreApplication.translate("MainWindow", u"Exit the application", None))
#endif // QT_CONFIG(statustip)
        self.actionPreferences.setText(QCoreApplication.translate("MainWindow", u"&Preferences...", None))
#if QT_CONFIG(statustip)
        self.actionPreferences.setStatusTip(QCoreApplication.translate("MainWindow", u"Open application preferences", None))
#endif // QT_CONFIG(statustip)
        self.actionZoomIn.setText(QCoreApplication.translate("MainWindow", u"Zoom &In", None))
#if QT_CONFIG(shortcut)
        self.actionZoomIn.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+=", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(statustip)
        self.actionZoomIn.setStatusTip(QCoreApplication.translate("MainWindow", u"Zoom in on the 3D view", None))
#endif // QT_CONFIG(statustip)
        self.actionZoomOut.setText(QCoreApplication.translate("MainWindow", u"Zoom &Out", None))
#if QT_CONFIG(shortcut)
        self.actionZoomOut.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+-", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(statustip)
        self.actionZoomOut.setStatusTip(QCoreApplication.translate("MainWindow", u"Zoom out from the 3D view", None))
#endif // QT_CONFIG(statustip)
        self.actionResetView.setText(QCoreApplication.translate("MainWindow", u"&Reset View", None))
#if QT_CONFIG(statustip)
        self.actionResetView.setStatusTip(QCoreApplication.translate("MainWindow", u"Reset the 3D view to default", None))
#endif // QT_CONFIG(statustip)
        self.actionAbout.setText(QCoreApplication.translate("MainWindow", u"&About 3D-MM", None))
#if QT_CONFIG(statustip)
        self.actionAbout.setStatusTip(QCoreApplication.translate("MainWindow", u"Show information about 3D-MM", None))
#endif // QT_CONFIG(statustip)
        self.viewer_widget.setPlainText(QCoreApplication.translate("MainWindow", u"3D Model Viewer\n"
"\n"
"This area will display the 3D model viewer component.\n"
"The viewer will be loaded dynamically at runtime.\n"
"\n"
"Features will include:\n"
"- Interactive 3D model rendering\n"
"- Multiple view modes (wireframe, solid, textured)\n"
"- Camera controls (orbit, pan, zoom)\n"
"- Lighting controls\n"
"- Measurement tools\n"
"- Animation playback\n"
"- Screenshot capture", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"&File", None))
        self.menuEdit.setTitle(QCoreApplication.translate("MainWindow", u"&Edit", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", u"&View", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"&Help", None))
        self.MainToolBar.setWindowTitle(QCoreApplication.translate("MainWindow", u"Main", None))
        self.MainToolBar.setObjectName(QCoreApplication.translate("MainWindow", u"MainToolBar", None))
        self.status_bar.setObjectName(QCoreApplication.translate("MainWindow", u"status_bar", None))
        self.status_label.setText(QCoreApplication.translate("MainWindow", u"Ready", None))
        self.memory_label.setText(QCoreApplication.translate("MainWindow", u"Memory: N/A", None))
        self.model_library_dock.setObjectName(QCoreApplication.translate("MainWindow", u"ModelLibraryDock", None))
        self.model_library_dock.setWindowTitle(QCoreApplication.translate("MainWindow", u"Model Library", None))
        self.model_library_widget.setPlainText(QCoreApplication.translate("MainWindow", u"Model Library\n"
"\n"
"This area will display the model library component.\n"
"The library widget will be loaded dynamically at runtime.\n"
"\n"
"Features will include:\n"
"- Model list with thumbnails\n"
"- Category filtering\n"
"- Search functionality\n"
"- Import/export options", None))
        self.properties_dock.setObjectName(QCoreApplication.translate("MainWindow", u"PropertiesDock", None))
        self.properties_dock.setWindowTitle(QCoreApplication.translate("MainWindow", u"Model Properties", None))
        self.properties_widget.setPlainText(QCoreApplication.translate("MainWindow", u"Model Properties\n"
"\n"
"This panel will display properties and metadata\n"
"for the selected 3D model.\n"
"\n"
"Features will include:\n"
"- Model information\n"
"- Metadata editing\n"
"- Tag management\n"
"- Export settings", None))
        self.metadata_dock.setObjectName(QCoreApplication.translate("MainWindow", u"MetadataDock", None))
        self.metadata_dock.setWindowTitle(QCoreApplication.translate("MainWindow", u"Metadata Editor", None))
        self.metadata_widget.setPlainText(QCoreApplication.translate("MainWindow", u"Metadata Editor\n"
"\n"
"This area will display the metadata editor component.\n"
"The editor widget will be loaded dynamically at runtime.\n"
"\n"
"Features will include:\n"
"- Title and description editing\n"
"- Category assignment\n"
"- Keyword tagging\n"
"- Custom properties", None))
    # retranslateUi

