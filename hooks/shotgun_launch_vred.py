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
        Bootstrap launches VRED Presenter with Shotgun Panel

        :param path: full path to the published file
        :param context: context object representing the publish
        """
        tk = sgtk.sgtk_from_path(path)
        software_launcher = sgtk.platform.create_engine_launcher(tk, context, "tk-vred")
        software_versions = software_launcher.scan_software()
        for version in software_versions:
            # TODO: Generate latest VRED version here
            if re.search("Presenter", version.product):
                launch_info = software_launcher.prepare_launch(version.path, "")
        env = os.environ.copy()
        for k in launch_info.environment:
            env[k] = launch_info.environment[k]
        try:
            subprocess.Popen([launch_info.path, launch_info.args, path], env=env)
        except RuntimeError:
            raise TankError(
                "Unable to launch VRED Presenter in context "
                "%r for file %s." % (context, path)
            )
