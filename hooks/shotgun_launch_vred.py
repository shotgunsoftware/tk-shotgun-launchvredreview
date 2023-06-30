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

        # save the current environment to be able to restore it later
        environ_clone = os.environ.copy()

        # modify the current environment to have all the mandatory information when launching the executable
        os.environ.update(launch_info.environment)
        os.environ["SGTK_CONTEXT"] = sgtk.context.serialize(context)

        # prepare the command to launch VRED Presenter with the right arguments
        cmd = f'start /B "App" "{launch_info.path}" {launch_info.args} {path}'

        try:
            os.system(cmd)
        except RuntimeError:
            raise TankError(
                "Unable to launch VRED Presenter in context "
                "%r for file %s." % (context, path)
            )
        finally:
            os.environ.clear()
            os.environ.update(environ_clone)

        return True
