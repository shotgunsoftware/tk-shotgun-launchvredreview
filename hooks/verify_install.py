# Copyright (c) 2020 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import re

import sgtk
from sgtk import TankError

HookBaseClass = sgtk.get_hook_baseclass()


class VerifyVREDInstall(HookBaseClass):
    def execute(self):
        """
        Verify VRED Presenter installation
        """
        tk = self.parent.sgtk
        context = self.parent.context
        try:
            software_launcher = sgtk.platform.create_engine_launcher(
                tk, context, "tk-vred"
            )
            software_versions = software_launcher.scan_for_presenter()
            if software_versions:
                presenter_versions = []
                for version in software_versions:
                    if re.search("Presenter", version.product):
                        presenter_versions.append(version)
                presenter_version = presenter_versions[-1]

                return presenter_version
            else:
                return None

        except RuntimeError:
            raise TankError("Unable to verify VRED Presenter installation.")
