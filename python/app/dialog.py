# Copyright (c) 2020 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import os

import sgtk

# by importing QT from sgtk rather than directly, we ensure that
# the code will be compatible with both PySide and PyQt.
from sgtk.platform.qt import QtCore, QtGui

# standard toolkit logger
logger = sgtk.platform.get_logger(__name__)


def show_dialog(app_instance):
    """
    Shows the main dialog window.
    """
    # in order to handle UIs seamlessly, each toolkit engine has methods for launching
    # different types of windows. By using these methods, your windows will be correctly
    # decorated and handled in a consistent fashion by the system.

    # we pass the dialog class to this method and leave the actual construction
    # to be carried out by toolkit.
    app_instance.engine.show_dialog(
        "Review with VRED Presenter", app_instance, AppDialog
    )


class AppDialog(QtGui.QWidget):
    """
    Main application dialog window
    """

    @property
    def hide_tk_title_bar(self):
        "Tell the system to not show the standard toolkit toolbar"
        return True

    def __init__(self, parent=None):
        super(AppDialog, self).__init__(parent)
        # get the current bundle
        self._app = sgtk.platform.current_bundle()
        self.title = "Review with VRED Help UI"
        self.initUI()

    def initUI(self):
        # Setup the UI
        self.setWindowTitle(self.title)
        self.layout = QtGui.QVBoxLayout()
        self.logo = QtGui.QLabel()
        self.logo.setPixmap(
            QtGui.QPixmap(os.path.join(self._app.disk_location, "icon_256.png"))
        )
        self.label1 = QtGui.QLabel()
        self.label1.setText(
            "Shotgun cannot find VRED Presenter on your system.<p>"
            "To use this feature, please contact your system "
            "administrator to get VRED Presenter installed on this computer.<br>"
            "Note: VRED Professional also includes an installation of "
            "VRED Presenter that can be used with Shotgun.<br>"
            "This functionality was introduced with the VRED2021.2 release.<p>"
            "<a href=https://www.autodesk.com/products/vred/features?#internal-link-vred-presenter>"
            "Learn more about VRED Presenter here.</a>"
        )
        self.label1.setOpenExternalLinks(True)
        self.layout.addWidget(self.logo)
        self.layout.addWidget(self.label1)
        self.setLayout(self.layout)
