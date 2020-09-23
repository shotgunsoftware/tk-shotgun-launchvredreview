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
import re

import sgtk
from sgtk.platform import Application
from sgtk import TankError
from sgtk import util
from tank_vendor.six.moves import urllib


class ReviewWithVRED(Application):
    """
    The app entry point. This class is responsible for initializing and tearing down
    the application, handle menu registration etc.
    """

    def init_app(self):
        """
        Called as the application is being initialized
        """
        # Assume we do not have VRED Presenter installed and change if / when
        # we find it.
        installed = False
        tk = sgtk.sgtk_from_entity("Project", self.context.project["id"])
        context = tk.context_from_entity("Project", self.context.project["id"])
        try:
            install_check = self.execute_hook(
                "hook_verify_install",
                tk=tk,
                context=context,
            )
        except TankError as e:
            self.log_error("Failed to check VRED installation: %s" % e)
            return

        # If we find it, change the logic and register the app the right way
        if install_check:
            installed = True

        if installed:
            app_payload = self.import_module("app")

            # Make sure we check on the permissions and platforms settings
            deny_permissions = self.get_setting("deny_permissions")
            deny_platforms = self.get_setting("deny_platforms")

            params = {
                "title": "Review with VRED",
                "deny_permissions": deny_permissions,
                "deny_platforms": deny_platforms,
                "supports_multiple_selection": False,
            }

            # now register the command with the engine
            self.engine.register_command(
                "Review with VRED", self._launch_via_hook, params
            )

        else:
            # Bring up the Help UI
            app_payload = self.import_module("app")
            menu_callback = lambda: app_payload.dialog.show_dialog(self)
            self.engine.register_command("Review with VRED", menu_callback)

    def _launch_via_hook(self, entity_type, entity_ids):

        published_file_entity_type = sgtk.util.get_published_file_entity_type(self.sgtk)

        if entity_type not in [published_file_entity_type, "Version"]:
            raise Exception(
                "Sorry, this app only works with entities of type %s or Version."
                % published_file_entity_type
            )

        if len(entity_ids) != 1:
            raise Exception("Action only accepts a single item.")

        if entity_type == "Version":
            # entity is a version so try to get the id
            # of the published file it is linked to:
            if published_file_entity_type == "PublishedFile":
                v = self.shotgun.find_one(
                    "Version", [["id", "is", entity_ids[0]]], ["published_files"]
                )
                if not v.get("published_files"):
                    self.log_error(
                        "Sorry, this can only be used on Versions with an associated Published File."
                    )
                    return
                publish_id = v["published_files"][0]["id"]
            else:  # == "TankPublishedFile":
                v = self.shotgun.find_one(
                    "Version", [["id", "is", entity_ids[0]]], ["tank_published_file"]
                )
                if not v.get("tank_published_file"):
                    self.log_error(
                        "Sorry, this can only be used on Versions with an associated Published File."
                    )
                    return
                publish_id = v["tank_published_file"]["id"]

        else:
            publish_id = entity_ids[0]

        # first get the path to the file on the local platform
        d = self.shotgun.find_one(
            published_file_entity_type,
            [["id", "is", publish_id]],
            ["path", "task", "entity"],
        )
        path_on_disk = d.get("path").get("local_path")

        # If this PublishedFile came from a zero config publish, it will
        # have a file URL rather than a local path.
        if path_on_disk is None:
            path_on_disk = d.get("path").get("url")
            if path_on_disk is not None:
                # We might have something like a %20, which needs to be
                # unquoted into a space, as an example.
                if "%" in path_on_disk:
                    path_on_disk = urllib.parse.unquote(path_on_disk)

                # If this came from a file url via a zero-config style publish
                # then we'll need to remove that from the head in order to end
                # up with the local disk path to the file.
                #
                # On Windows, we will have a path like file:///E:/path/to/file.jpg
                # and we need to ditch all three of the slashes at the head. On
                # other operating systems it will just be file:///path/to/file.jpg
                # and we will want to keep the leading slash.
                if util.is_windows():
                    pattern = r"^file:///"
                else:
                    pattern = r"^file://"

                path_on_disk = re.sub(pattern, "", path_on_disk)
            else:
                self.log_error(
                    "Unable to determine the path on disk for entity id=%s."
                    % publish_id
                )

        # first check if we should pass this to the viewer
        # hopefully this will cover most image sequence types
        # any image sequence types not passed to the viewer
        # will fail later when we check if the file exists on disk
        for x in self.get_setting("viewer_extensions", {}):
            if path_on_disk.endswith(".%s" % x):
                self.log_error("File is of type %s" % x)
            else:
                self.log_info("File type does not work for Review with VRED.")
                return

        # check that it exists
        if not os.path.exists(path_on_disk):
            self.log_error(
                "The file associated with this publish, "
                "%s, cannot be found on disk!" % path_on_disk
            )
            return

        # now get the context - try to be as inclusive as possible here:
        # start with the task, if that doesn't work, fall back onto the path
        # this is because some paths don't include all the metadata that
        # is contained inside the publish record (e.g typically not the task)
        if d.get("task"):
            ctx = self.sgtk.context_from_entity("Task", d.get("task").get("id"))
        else:
            ctx = self.sgtk.context_from_path(path_on_disk)

        # call out to the hook
        try:
            launched = self.execute_hook(
                "hook_launch_publish",
                path=path_on_disk,
                context=ctx,
            )
        except TankError as e:
            self.log_error("Failed to launch VRED for this published file: %s" % e)
            return

        if launched:
            self.log_info("Successfully launched Review with VRED.")
        else:
            self.log_info("There was an error launching Review with VRED.")
