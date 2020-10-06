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
import subprocess
import re

import sgtk
from sgtk import TankError

HookBaseClass = sgtk.get_hook_baseclass()


class LaunchWithVRED(HookBaseClass):
    def execute(self, path, context):
        """
        Bootstrap launches VRED Presenter

        :param path: full path to the published file
        :param context: context object representing the publish
        """
        tk = self.parent.sgtk
        software_launcher = sgtk.platform.create_engine_launcher(tk, context, "tk-vred")
        software_versions = software_launcher.scan_for_presenter()
        presenter_versions = []
        for version in software_versions:
            if re.search("Presenter", version.product):
                presenter_versions.append(version)
        presenter_version = presenter_versions[-1]
        launch_info = software_launcher.prepare_launch(presenter_version.path, "")
        env = os.environ.copy()
        for k in launch_info.environment:
            if k == "SGTK_CONTEXT":
                env[k] = sgtk.context.serialize(context)
            else:
                env[k] = str(launch_info.environment[k])
        try:
            launched = subprocess.Popen(
                [launch_info.path, launch_info.args, path], env=env
            )
        except RuntimeError:
            raise TankError(
                "Unable to launch VRED Presenter in context "
                "%r for file %s." % (context, path)
            )
        if launched:
            return True
        else:
            return False
