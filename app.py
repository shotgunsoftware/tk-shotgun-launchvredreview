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

        # first, we use the special import_module command to access the app module
        # that resides inside the python folder in the app. This is where the actual UI
        # and business logic of the app is kept. By using the import_module command,
        # toolkit's code reload mechanism will work properly.
        app_payload = self.import_module("app")

        # now register a *command*, which is normally a menu entry of some kind on a Shotgun
        # menu (but it depends on the engine). The engine will manage this command and
        # whenever the user requests the command, it will call out to the callback.

        # first, set up our callback, calling out to a method inside the app module contained
        # in the python folder of the app
        menu_callback = lambda: app_payload.dialog.show_dialog(self)

        # Make sure we check on the permissions and platforms settings
        deny_permissions = self.get_setting("deny_permissions")
        deny_platforms = self.get_setting("deny_platforms")

        params = {
            "title": "Review with VRED.",
            "deny_permissions": deny_permissions,
            "deny_platforms": deny_platforms,
            "supports_multiple_selection": False,
        }

        # now register the command with the engine
        self.engine.register_command("Review with VRED", self._launch_via_hook, params)

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
