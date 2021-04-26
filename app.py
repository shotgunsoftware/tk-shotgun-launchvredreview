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
        Called as the application is being initialized.
        """

        try:
            installed = self.execute_hook("hook_verify_install")
        except TankError as error:
            # Log an error and return immediately on failure to find VRED installation.
            self.log_error("Failed to check VRED installation: {}".format(error))
            return

        if installed:
            # Make sure we check on the permissions and platforms settings
            deny_permissions = self.get_setting("deny_permissions")
            deny_platforms = self.get_setting("deny_platforms")
            params = {
                "title": "Review with VRED",
                "deny_permissions": deny_permissions,
                "deny_platforms": deny_platforms,
                "supports_multiple_selection": False,
            }

            # Now register the command with the engine
            self.engine.register_command(
                "Review with VRED", self._launch_via_hook, params
            )
        else:
            # No installatino found, bring up the Help UI
            app_payload = self.import_module("app")
            menu_callback = lambda: app_payload.dialog.show_dialog(self)
            self.engine.register_command("Review with VRED", menu_callback)

    def _launch_via_hook(self, entity_type, entity_ids):
        """
        Executes the "hook_launch_publish" hook, passing a context and file path params
        that are extracted from process the entity passed in. This method only supports
        entity typess: PublishedFile entity type, Version and Playlist. For each entity
        type, the context passed to the hook will be the entity passed in to this method.
        The file path will be determined based on the entity type:
            PublishedFile entity types: file path will be the PublishedFile's path itself
            Version: file path will be the latest PublishedFile whose PublishedFileType
                     is in the accepted list. The "latest" PublishedFile is determined by
                     the PublishedFile with the highest version.
            Playlist: file path will be empty (""). For now, no Version is autoamatically
                      loaded for review, the user will be shown the Version list to select
                      from to load first.

        :param entity_type: The type of the entities.
        :param entity_ids: The list of ids of the entities
        """

        if not entity_ids:
            self.log_warning("No entity was passed - returning immediately.")
            return

        if len(entity_ids) > 1:
            raise TankError("Action only accepts a single item.")

        entity_id = entity_ids[0]
        published_file = self._get_published_file_from_entity(entity_type, entity_id)

        if published_file is None:
            # Published file for entity was not found
            raise TankError(
                "Sorry, this can only be used on an entity with an associated published file."
            )

        if published_file.get("error", None) is not None:
            # There was an error getting the published file from the entity
            raise TankError(published_file["error"])

        # Extract the path on local disk for the published file that will be opened in VRED
        # for review
        path_on_disk = _get_published_file_path(published_file)

        if path_on_disk is None:
            raise TankError(
                "Unable to determine the path on disk for published file with id '{}'.".format(
                    published_file["id"]
                )
            )

        # Only check the path on disk if there is one. The user is allowed launch VRED with no
        # initial file path.
        if path_on_disk and not os.path.exists(path_on_disk):
            raise TankError(
                "The file associated with this publish '{}' cannot be found on disk!".format(
                    path_on_disk
                )
            )

        # Get a context object based on the entity passed to this method
        ctx = self.sgtk.context_from_entity(entity_type, entity_id)
        try:
            if self.execute_hook("hook_launch_publish", path=path_on_disk, context=ctx):
                self.log_info("Successfully launched Review with VRED.")
            else:
                self.log_error("Failed to launch Review with VRED.")

        except TankError as error:
            self.log_error(
                "An error occurred when attempting to launch VRED for this published file: {}".format(
                    error
                )
            )

    def _get_published_file_from_entity(self, entity_type, entity_id):
        """
        Return the published file associated with the given entity. Supported entity types:
        the published entity type defined by the pipeline configuration, "Version" and "Playlist".

        published entity type: The object for `entity_type` and `entity_id` will be returned.
        "Version": The published file with the highest version will be returned
        "Playlist": No published file object will be returned

        :param entity_type: The entity type
        :param entity_id: The entity id
        """

        published_file = None
        published_file_entity_type = sgtk.util.get_published_file_entity_type(self.sgtk)

        if entity_type == published_file_entity_type:
            published_file = self.shotgun.find_one(
                published_file_entity_type,
                [["id", "is", entity_id]],
                fields=["id", "path"],
            )

        elif entity_type == "Version":
            filters = [["version", "is", {"type": "Version", "id": entity_id}]]
            # Attempt to get the filter for Published File Types from the tk-vred engine settings. If an error
            # occurs, or no such settings was found, Published Files of any type will be queried.
            try:
                tk = sgtk.sgtk_from_entity(
                    self.context.project["type"], self.context.project["id"]
                )
                env = sgtk.platform.engine.get_environment_from_context(
                    tk, self.context
                )
                engine_settings = env.get_engine_settings("tk-vred")
                accepted_published_file_types = engine_settings.get(
                    "accepted_published_file_types"
                )
                if accepted_published_file_types:
                    filters.append(
                        [
                            "published_file_type.PublishedFileType.code",
                            "in",
                            accepted_published_file_types,
                        ]
                    )
            except Exception as error:
                self.logger.warning(
                    "Failed to retrieve 'accepted_published_file_types' filter setting. Retrieving Published Files of any type.\n\n{e}".format(
                        e=error
                    )
                )

            # Retrieve the lastest Published File (highest version) for this Version
            published_files = self.shotgun.find(
                published_file_entity_type,
                filters,
                fields=["id", "path", "published_file_type"],
                order=[{"field_name": "version_number", "direction": "desc"}],
            )

            if not published_files:
                published_file = {
                    "error": "Version has no published files to load for review."
                }

            elif len(published_files) != 1:
                published_file = {
                    "error": "Failed to load Version for review with VRED because there is more than one PublishedFile entity with the same PublishedFileType associated for this Version."
                }

            else:
                published_file = published_files[0]

        elif entity_type == "Playlist":
            # TODO get the last added version to the playlist and open the associatd published file
            # This requires opening SG Panel with a Playlist context, and then switching to the
            # Version to automatically start reviewing
            published_file = {}

        else:
            # Unsupported entity type, return error inside dictionary result
            published_file = {
                "error": "Sorry, this app only works with entities of type {}, Version or Playlist.".format(
                    published_file_entity_type
                )
            }

        return published_file


def _get_published_file_path(published_file):
    """
    Return the path on disk for the given published file.

    :param published_file: The PublishedFile entity
    """

    if published_file is None:
        return None

    path = published_file.get("path", None)
    if path is None:
        return ""

    # Return the local path right away, if we have it
    if path.get("local_path", None) is not None:
        return path["local_path"]

    # This published file came from a zero config publish, it will
    # have a file URL rather than a local path.
    path_on_disk = path.get("url", None)
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

    return path_on_disk
