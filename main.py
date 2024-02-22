from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction

import sys
import shutil
import logging
import subprocess


class X11WindowSwitcherExtension(Extension):
    def __init__(self):
        logger = logging.getLogger(__name__)

        # Check that wmctrl is installed
        if shutil.which("wmctrl"):
            # We have wmctrl, hook up extension
            super(X11WindowSwitcherExtension, self).__init__()

            self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        else:
            # No wmctrl, so bail
            logger.error("Missing Dependency: wmctrl not found on $PATH")

            sys.exit()


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        search = str(event.get_argument() or "").lower().strip()

        items = []

        # Get list of all windows, and process into a dictionary that looks like this:
        # {<window_id>: {ws: <workspace_id>, name: <window_name>}}
        result = subprocess.run(
            ['wmctrl -l | awk \'{$3=""; print $0}\''],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # Equivalent to capture_output=True
            shell=True,
            universal_newlines=True,  # Equivalent to text=True
        ).stdout

        window_list = [y for y in (x.strip() for x in result.split("\n")) if y]

        window_dict = {
            x[1].split(maxsplit=2)[0]: {
                "ws": int(x[1].split(maxsplit=2)[1]),
                "name": x[1].split(maxsplit=2)[2],
            }
            for x in enumerate(window_list)
        }

        # Filter the Ulauncher window itself out
        filtered_window_dict = {
            key: value for key, value in window_dict.items()
            if value.get("name") != "Ulauncher - Application Launcher"
        }

        for window_id, window in filtered_window_dict.items():

            if search == "" or search in window["name"].lower():
                items.append(
                    ExtensionResultItem(
                        icon="images/window.svg",
                        name=window["name"],
                        description="Workspace {}, Window Id: {}".format(
                            window["ws"], window_id
                        ),
                        on_enter=RunScriptAction("wmctrl -ia {}".format(window_id)),
                    )
                )

        return RenderResultListAction(items)


if __name__ == "__main__":
    X11WindowSwitcherExtension().run()
