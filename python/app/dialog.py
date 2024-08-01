# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from tank.platform.qt import QtCore

for name, cls in QtCore.__dict__.items():
    if isinstance(cls, type):
        globals()[name] = cls

from tank.platform.qt import QtGui

for name, cls in QtGui.__dict__.items():
    if isinstance(cls, type):
        globals()[name] = cls


from . import resources_rc


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(431, 392)
        self.horizontalLayout = QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.logo_example = QLabel(Dialog)
        self.logo_example.setObjectName("logo_example")
        self.logo_example.setPixmap(QPixmap(":/res/sg_logo.png"))

        self.horizontalLayout.addWidget(self.logo_example)

        self.context = QLabel(Dialog)
        self.context.setObjectName("context")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.context.sizePolicy().hasHeightForWidth())
        self.context.setSizePolicy(sizePolicy)
        self.context.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.context)

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)

    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(
            QCoreApplication.translate("Dialog", "The Current Sgtk Environment", None)
        )
        self.logo_example.setText("")
        self.context.setText(
            QCoreApplication.translate("Dialog", "Your Current Context: ", None)
        )

    # retranslateUi
