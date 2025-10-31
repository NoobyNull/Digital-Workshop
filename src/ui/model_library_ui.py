# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'model_library.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QListView,
    QProgressBar, QPushButton, QSizePolicy, QSplitter,
    QTabWidget, QTableView, QToolButton, QTreeView,
    QVBoxLayout, QWidget)

class Ui_ModelLibraryWidget(object):
    def setupUi(self, ModelLibraryWidget):
        if not ModelLibraryWidget.objectName():
            ModelLibraryWidget.setObjectName(u"ModelLibraryWidget")
        ModelLibraryWidget.resize(1000, 700)
        self.main_layout = QVBoxLayout(ModelLibraryWidget)
        self.main_layout.setSpacing(5)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.toolbar_frame = QFrame(ModelLibraryWidget)
        self.toolbar_frame.setObjectName(u"toolbar_frame")
        self.toolbar_frame.setFrameShape(QFrame.NoFrame)
        self.toolbar_frame.setFrameShadow(QFrame.Plain)
        self.toolbar_layout = QHBoxLayout(self.toolbar_frame)
        self.toolbar_layout.setObjectName(u"toolbar_layout")
        self.toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self.view_label = QLabel(self.toolbar_frame)
        self.view_label.setObjectName(u"view_label")

        self.toolbar_layout.addWidget(self.view_label)

        self.list_view_button = QToolButton(self.toolbar_frame)
        self.list_view_button.setObjectName(u"list_view_button")
        self.list_view_button.setCheckable(True)
        self.list_view_button.setChecked(True)

        self.toolbar_layout.addWidget(self.list_view_button)

        self.grid_view_button = QToolButton(self.toolbar_frame)
        self.grid_view_button.setObjectName(u"grid_view_button")
        self.grid_view_button.setCheckable(True)

        self.toolbar_layout.addWidget(self.grid_view_button)

        self.toolbar_spacer = QFrame(self.toolbar_frame)
        self.toolbar_spacer.setObjectName(u"toolbar_spacer")
        self.toolbar_spacer.setFrameShape(QFrame.NoFrame)
        self.toolbar_spacer.setFrameShadow(QFrame.Plain)

        self.toolbar_layout.addWidget(self.toolbar_spacer)

        self.import_button = QPushButton(self.toolbar_frame)
        self.import_button.setObjectName(u"import_button")

        self.toolbar_layout.addWidget(self.import_button)

        self.refresh_button = QPushButton(self.toolbar_frame)
        self.refresh_button.setObjectName(u"refresh_button")

        self.toolbar_layout.addWidget(self.refresh_button)


        self.main_layout.addWidget(self.toolbar_frame)

        self.search_widget_placeholder = QWidget(ModelLibraryWidget)
        self.search_widget_placeholder.setObjectName(u"search_widget_placeholder")
        self.search_widget_placeholder.setMinimumSize(QSize(0, 50))

        self.main_layout.addWidget(self.search_widget_placeholder)

        self.content_splitter = QSplitter(ModelLibraryWidget)
        self.content_splitter.setObjectName(u"content_splitter")
        self.content_splitter.setOrientation(Qt.Horizontal)
        self.file_browser_group = QGroupBox(self.content_splitter)
        self.file_browser_group.setObjectName(u"file_browser_group")
        self.file_browser_layout = QVBoxLayout(self.file_browser_group)
        self.file_browser_layout.setObjectName(u"file_browser_layout")
        self.path_frame = QFrame(self.file_browser_group)
        self.path_frame.setObjectName(u"path_frame")
        self.path_frame.setFrameShape(QFrame.NoFrame)
        self.path_frame.setFrameShadow(QFrame.Plain)
        self.path_layout = QHBoxLayout(self.path_frame)
        self.path_layout.setObjectName(u"path_layout")
        self.path_layout.setContentsMargins(0, 0, 0, 0)
        self.path_label = QLabel(self.path_frame)
        self.path_label.setObjectName(u"path_label")

        self.path_layout.addWidget(self.path_label)

        self.path_display = QLabel(self.path_frame)
        self.path_display.setObjectName(u"path_display")

        self.path_layout.addWidget(self.path_display)


        self.file_browser_layout.addWidget(self.path_frame)

        self.file_tree = QTreeView(self.file_browser_group)
        self.file_tree.setObjectName(u"file_tree")
        self.file_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.file_tree.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.file_browser_layout.addWidget(self.file_tree)

        self.content_splitter.addWidget(self.file_browser_group)
        self.model_view_group = QGroupBox(self.content_splitter)
        self.model_view_group.setObjectName(u"model_view_group")
        self.model_view_layout = QVBoxLayout(self.model_view_group)
        self.model_view_layout.setObjectName(u"model_view_layout")
        self.view_tabs = QTabWidget(self.model_view_group)
        self.view_tabs.setObjectName(u"view_tabs")
        self.list_tab = QWidget()
        self.list_tab.setObjectName(u"list_tab")
        self.list_tab_layout = QVBoxLayout(self.list_tab)
        self.list_tab_layout.setSpacing(0)
        self.list_tab_layout.setObjectName(u"list_tab_layout")
        self.list_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.list_view = QTableView(self.list_tab)
        self.list_view.setObjectName(u"list_view")
        self.list_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_view.setSelectionBehavior(QTableView.SelectRows)
        self.list_view.setAlternatingRowColors(True)
        self.list_view.setSortingEnabled(True)
        self.list_view.horizontalHeader().setStretchLastSection(False)

        self.list_tab_layout.addWidget(self.list_view)

        self.view_tabs.addTab(self.list_tab, "")
        self.grid_tab = QWidget()
        self.grid_tab.setObjectName(u"grid_tab")
        self.grid_tab_layout = QVBoxLayout(self.grid_tab)
        self.grid_tab_layout.setSpacing(0)
        self.grid_tab_layout.setObjectName(u"grid_tab_layout")
        self.grid_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_view = QListView(self.grid_tab)
        self.grid_view.setObjectName(u"grid_view")
        self.grid_view.setViewMode(QListView.IconMode)
        self.grid_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.grid_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.grid_view.setResizeMode(QListView.Adjust)
        self.grid_view.setSpacing(10)
        self.grid_view.setUniformItemSizes(True)

        self.grid_tab_layout.addWidget(self.grid_view)

        self.view_tabs.addTab(self.grid_tab, "")

        self.model_view_layout.addWidget(self.view_tabs)

        self.content_splitter.addWidget(self.model_view_group)

        self.main_layout.addWidget(self.content_splitter)

        self.status_frame = QFrame(ModelLibraryWidget)
        self.status_frame.setObjectName(u"status_frame")
        self.status_frame.setFrameShape(QFrame.NoFrame)
        self.status_frame.setFrameShadow(QFrame.Plain)
        self.status_layout = QHBoxLayout(self.status_frame)
        self.status_layout.setObjectName(u"status_layout")
        self.status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_label = QLabel(self.status_frame)
        self.status_label.setObjectName(u"status_label")

        self.status_layout.addWidget(self.status_label)

        self.model_count_label = QLabel(self.status_frame)
        self.model_count_label.setObjectName(u"model_count_label")

        self.status_layout.addWidget(self.model_count_label)

        self.progress_bar = QProgressBar(self.status_frame)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        self.status_layout.addWidget(self.progress_bar)


        self.main_layout.addWidget(self.status_frame)


        self.retranslateUi(ModelLibraryWidget)

        self.view_tabs.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ModelLibraryWidget)
    # setupUi

    def retranslateUi(self, ModelLibraryWidget):
        ModelLibraryWidget.setWindowTitle(QCoreApplication.translate("ModelLibraryWidget", u"Model Library", None))
        self.view_label.setText(QCoreApplication.translate("ModelLibraryWidget", u"View:", None))
        self.list_view_button.setText(QCoreApplication.translate("ModelLibraryWidget", u"List View", None))
#if QT_CONFIG(tooltip)
        self.list_view_button.setToolTip(QCoreApplication.translate("ModelLibraryWidget", u"Show models in list view", None))
#endif // QT_CONFIG(tooltip)
        self.grid_view_button.setText(QCoreApplication.translate("ModelLibraryWidget", u"Grid View", None))
#if QT_CONFIG(tooltip)
        self.grid_view_button.setToolTip(QCoreApplication.translate("ModelLibraryWidget", u"Show models in grid view", None))
#endif // QT_CONFIG(tooltip)
        self.import_button.setText(QCoreApplication.translate("ModelLibraryWidget", u"Import Models...", None))
#if QT_CONFIG(tooltip)
        self.import_button.setToolTip(QCoreApplication.translate("ModelLibraryWidget", u"Import models from files or folders", None))
#endif // QT_CONFIG(tooltip)
        self.refresh_button.setText(QCoreApplication.translate("ModelLibraryWidget", u"Refresh", None))
#if QT_CONFIG(tooltip)
        self.refresh_button.setToolTip(QCoreApplication.translate("ModelLibraryWidget", u"Refresh model library", None))
#endif // QT_CONFIG(tooltip)
        self.file_browser_group.setTitle(QCoreApplication.translate("ModelLibraryWidget", u"File Browser", None))
        self.path_label.setText(QCoreApplication.translate("ModelLibraryWidget", u"Path:", None))
        self.path_display.setText(QCoreApplication.translate("ModelLibraryWidget", u"C:\\", None))
        self.model_view_group.setTitle(QCoreApplication.translate("ModelLibraryWidget", u"Models", None))
        self.view_tabs.setTabText(self.view_tabs.indexOf(self.list_tab), QCoreApplication.translate("ModelLibraryWidget", u"List", None))
        self.view_tabs.setTabText(self.view_tabs.indexOf(self.grid_tab), QCoreApplication.translate("ModelLibraryWidget", u"Grid", None))
        self.status_label.setText(QCoreApplication.translate("ModelLibraryWidget", u"Ready", None))
        self.model_count_label.setText(QCoreApplication.translate("ModelLibraryWidget", u"Models: 0", None))
    # retranslateUi

