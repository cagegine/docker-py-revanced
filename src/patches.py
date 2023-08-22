"""Revanced Patches."""

import contextlib
import json
from typing import Any, Dict, List, Tuple

from loguru import logger

from src.app import APP
from src.config import RevancedConfig
from src.exceptions import AppNotFound, PatchesJsonLoadFailed


class Patches(object):
    """Revanced Patches."""

    _revanced_app_ids = {
        "com.reddit.frontpage": "reddit",
        "com.ss.android.ugc.trill": "tiktok",
        "com.twitter.android": "twitter",
        "de.dwd.warnapp": "warnwetter",
        "com.spotify.music": "spotify",
        "com.awedea.nyx": "nyx-music-player",
        "ginlemon.iconpackstudio": "icon_pack_studio",
        "com.ticktick.task": "ticktick",
        "tv.twitch.android.app": "twitch",
        "com.myprog.hexedit": "hex-editor",
        "co.windyapp.android": "windy",
        "org.totschnig.myexpenses": "my-expenses",
        "com.backdrops.wallpapers": "backdrops",
        "com.ithebk.expensemanager": "expensemanager",
        "net.dinglisch.android.taskerm": "tasker",
        "net.binarymode.android.irplus": "irplus",
        "com.vsco.cam": "vsco",
        "com.zombodroid.MemeGenerator": "meme-generator-free",
        "com.teslacoilsw.launcher": "nova_launcher",
        "eu.faircode.netguard": "netguard",
        "com.instagram.android": "instagram",
        "com.nis.app": "inshorts",
        "com.facebook.orca": "messenger",
        "com.google.android.apps.recorder": "grecorder",
        "tv.trakt.trakt": "trakt",
        "com.candylink.openvpn": "candyvpn",
        "com.sony.songpal.mdr": "sonyheadphone",
        "com.dci.dev.androidtwelvewidgets": "androidtwelvewidgets",
        "io.yuka.android": "yuka",
        "free.reddit.news": "relay",
        "com.rubenmayayo.reddit": "boost",
        "com.andrewshu.android.reddit": "rif",
        "com.laurencedawson.reddit_sync": "sync",
        "ml.docilealligator.infinityforreddit": "infinity",
        "me.ccrama.redditslide": "slide",
        "com.onelouder.baconreader": "bacon",
        "com.google.android.youtube": "youtube",
        "com.google.android.apps.youtube.music": "youtube_music",
        "com.mgoogle.android.gms": "microg",
        "jp.pxv.android": "pixiv",
    }
    revanced_app_ids = {
        key: (value, "_" + value) for key, value in _revanced_app_ids.items()
    }

    @staticmethod
    def get_package_name(app: str) -> str:
        """The function `get_package_name` takes an app name as input and
        returns the corresponding package name, or raises an exception if the
        app is not supported.

        Parameters
        ----------
        app : str
            The `app` parameter is a string that represents the name of an app.

        Returns
        -------
            a string, which is the package name corresponding to the given app name.
        """
        for package, app_tuple in Patches.revanced_app_ids.items():
            if app_tuple[0] == app:
                return package
        raise AppNotFound(f"App {app} not supported yet.")

    @staticmethod
    def support_app() -> Dict[str, str]:
        """The function `support_app()` returns a dictionary of supported app
        IDs.

        Returns
        -------
            a dictionary of supported apps.
        """
        return Patches._revanced_app_ids

    def fetch_patches(self, config: RevancedConfig, app: APP) -> None:
        """The function fetches patches from a JSON file and organizes them
        based on compatibility with different applications.

        Parameters
        ----------
        config : RevancedConfig
            The `config` parameter is of type `RevancedConfig` and represents the configuration for the
        application.
        app : APP
            The `app` parameter is of type `APP`. It represents an instance of the `APP` class.
        """
        patch_loader = PatchLoader()
        patches = patch_loader.load_patches(
            f'{config.temp_folder}/{app.resource["patches_json"]}'
        )
        for app_name in (self.revanced_app_ids[x][1] for x in self.revanced_app_ids):
            setattr(self, app_name, [])
        setattr(self, "universal_patch", [])

        for patch in patches:
            if not patch["compatiblePackages"]:
                p = {x: patch[x] for x in ["name", "description"]}
                p["app"] = "universal"
                p["version"] = "all"
                getattr(self, "universal_patch").append(p)
            for compatible_package, version in [
                (x["name"], x["versions"]) for x in patch["compatiblePackages"]
            ]:
                if compatible_package in self.revanced_app_ids:
                    app_name = self.revanced_app_ids[compatible_package][1]
                    p = {x: patch[x] for x in ["name", "description"]}
                    p["app"] = compatible_package
                    p["version"] = version[-1] if version else "all"
                    getattr(self, app_name).append(p)
        n_patches = len(getattr(self, f"_{app.app_name}"))
        app.no_of_patches = n_patches

    def __init__(self, config: RevancedConfig, app: APP) -> None:
        self.fetch_patches(config, app)

    def get(self, app: str) -> Tuple[List[Dict[str, str]], str]:
        """The function `get` retrieves all patches for a given application and
        returns them along with the latest version.

        Parameters
        ----------
        app : str
            The `app` parameter is a string that represents the name of the application for which you want
        to retrieve patches.

        Returns
        -------
            a tuple containing two elements. The first element is a list of dictionaries representing
        patches for the given app. The second element is a string representing the version of the
        patches.
        """
        app_names = {value[0]: value[1] for value in self.revanced_app_ids.values()}

        if not (app_name := app_names.get(app)):
            raise AppNotFound(f"App {app} not supported yet.")

        patches = getattr(self, app_name)
        version = "latest"
        with contextlib.suppress(StopIteration):
            version = next(i["version"] for i in patches if i["version"] != "all")
        return patches, version

    def include_exclude_patch(
        self, app: APP, parser: Any, patches: List[Dict[str, str]]
    ) -> None:
        """The function `include_exclude_patch` includes and excludes patches
        for a given app based on certain conditions.

        Parameters
        ----------
        app : APP
            The "app" parameter is the name of the app for which the patches are being included or
        excluded.
        parser : Any
            The `parser` parameter is an object of type `Any`, which means it can be any type of object. It
        is used to perform parsing operations.
        patches : List[Dict[str, str]]
            A list of dictionaries, where each dictionary represents a patch and contains the following
        keys:
        """
        for patch in patches:
            normalized_patch = patch["name"].lower().replace(" ", "-")
            parser.include(
                normalized_patch
            ) if normalized_patch not in app.exclude_request else parser.exclude(
                normalized_patch
            )
        for normalized_patch in app.include_request:
            parser.include(normalized_patch) if normalized_patch not in getattr(
                self, "universal_patch", []
            ) else ()

    def get_app_configs(self, app: "APP") -> List[Dict[str, str]]:
        """The function `get_app_configs` retrieves configurations for a given
        app, including patches, version information, and whether it is
        experimental.

        Parameters
        ----------
        app : "APP"
            The "app" parameter is the name of the application for which you want to get the
        configurations.

        Returns
        -------
            the total_patches, which is a list of dictionaries containing information about the patches for
        the given app. Each dictionary in the list contains the keys "Patches", "Version", and
        "Experimental".
        """
        experiment = False
        total_patches, recommended_version = self.get(app=app.app_name)
        if app.app_version:
            logger.debug(f"Picked {app} version {app.app_version:} from env.")
            if (
                app.app_version == "latest"
                or app.app_version > recommended_version
                or app.app_version < recommended_version
            ):
                experiment = True
            recommended_version = app.app_version
        app.set_recommended_version(recommended_version, experiment)
        return total_patches


class PatchLoader:
    """Patch Loader."""

    @staticmethod
    def load_patches(file_name: str) -> Any:
        """The function `load_patches` loads patches from a file and returns
        them.

        Parameters
        ----------
        file_name : str
            The `file_name` parameter is a string that represents the name or path of the file from which
        the patches will be loaded.

        Returns
        -------
            the patches loaded from the file.
        """
        try:
            with open(file_name) as f:
                patches = json.load(f)
            return patches
        except FileNotFoundError as e:
            raise PatchesJsonLoadFailed("File not found", file_name=file_name) from e
