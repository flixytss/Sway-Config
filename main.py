import os, json, sys, subprocess, math

WORKING_DIR = "/home/danielpag/.config/sway"
# WORKING_DIR = "." # Only for debugging

# User experience configs
POINTER_SPEED           = "0.2"
POINTER_ACCELERATION    = False

BROWSER     = "firefox"
TERMINAL    = "ghostty"
SUPER_KEY   = "Mod4"
FILE_EXPLORER = "dolphin"
MENU_EXECUTABLE = "rofi -show drun"
SCREENSHOT_APP = "grim"

KEYBOARD_LAYOUT = "es"

variables: dict = {}
keybinds: dict = {}
general: dict = {}
monitors: dict = {}
execapps: dict = {}

directions = [
    "Left",
    "Down",
    "Up",
    "Right"
]

CustomVars = {
    "mod": SUPER_KEY,
    "term": TERMINAL,
    "browser": BROWSER,
    "files_manager": FILE_EXPLORER,
    "menu": MENU_EXECUTABLE,
    "scrshot": SCREENSHOT_APP,
}
Customkeybinds = {
    "$mod+b": ["exec", "$browser"],
    "$mod+e": ["exec", "$files_manager"],
    "$mod+f": ["fullscreen"],
    "$mod+q": ["kill"],
    "$mod+Return": ["exec", "$term"],
    "$mod+Space": ["exec", "$menu"],
    "$mod+v": ["floating", "toggle"],
    "--locked XF86AudioPlay": ["exec", "playerctl", "play-pause"],
    "--locked XF86AudioPause": ["exec", "playerctl", "play-pause"],
    "--locked XF86AudioPrev": ["exec", "playerctl", "previous"],
    "--locked XF86AudioNext": ["exec", "playerctl", "next"],
    "--locked XF86AudioStop": ["exec", "playerctl", "stop"],
    "--locked XF86MonBrightnessDown": ["exec", "brightnessctl", "set", "5%-"],
    "--locked XF86MonBrightnessUp": ["exec", "brightnessctl", "set", "5%+"],
    "--locked XF86AudioMute": ["exec", "pactl", "set-sink-mute", "\\@DEFAULT_SINK@", "toggle"],
    "--locked XF86AudioLowerVolume": ["exec", "pactl", "set-sink-volume", "\\@DEFAULT_SINK@", "-5%"],
    "--locked XF86AudioRaiseVolume": ["exec", "pactl", "set-sink-volume", "\\@DEFAULT_SINK@", "+5%"],
    "--locked XF86AudioMicMute": ["exec", "pactl", "set-source-mute", "\\@DEFAULT_SINK@", "toggle"],
    "Print": ["exec", "$scrshot"],
    "$mod+Shift+c": ["reload"],
}
CustomGenerals = {
    "input type:pointer": [ ["accel_profile", "adaptive" if POINTER_ACCELERATION else "flat"], ["pointer_accel", POINTER_SPEED] ],
    "input type:keyboard": [ ["xkb_layout", KEYBOARD_LAYOUT] ],
    "floating_modifier $mod normal": [],
    
    # Customization
    "default_border none": [],
    "default_floating_border none": [],
    "client.focused          #7aa2f7  #1f2335    #ffffff #1a1b26  #7aa2f7": [],
    "client.focused_inactive #3b4261  #292e42    #c0caf5 #3b4261  #3b4261": [],
    "client.unfocused        #1a1b26  #1a1b26    #565f89 #1a1b26  #1a1b26": [],
    "client.urgent           #f7768e  #f7768e    #ffffff #f7768e  #f7768e": [],
    "client.placeholder      #1a1b26  #1a1b26    #565f89 #1a1b26  #1a1b26": [],
    "client.background       #1a1b26": [],
}
CustomMonitors = {}

CustomExecApps = [
    "waybar",
    """hash dbus-update-activation-environment 2>/dev/null && \\
     dbus-update-activation-environment --systemd DISPLAY \\
                                                  SWAYSOCK \\
                                                  XDG_CURRENT_DESKTOP=sway \\
                                                  WAYLAND_DISPLAY""",
    """systemctl --user import-environment DISPLAY \\
                                         SWAYSOCK \\
                                         WAYLAND_DISPLAY \\
                                         XDG_CURRENT_DESKTOP""",
    "systemctl --user set-environment XDG_CURRENT_DESKTOP=sway"
]

def AppendToConfig(name: str, var: str, args: list):
    os.system("touch " + WORKING_DIR + "/configs/" + name + ".json")

    with open(WORKING_DIR + "/configs/" + name + ".json", "r+") as conf:
        buffer: dict = {}
        try: buffer = json.loads(conf.read())
        except: pass
        try: buffer[var]
        except KeyError: buffer[var] = []

        buffer[var].append(args)

        conf.seek(0, 0)
        conf.write(json.dumps(buffer, indent=4))
        conf.truncate()

def ReadConfig(name: str):
    try:
        with open(WORKING_DIR + "/configs/" + name + ".json", "r") as conf:
            load: dict = {}
            try: load = json.loads(conf.read())
            except: pass
            return load
    except FileNotFoundError:
        match name:
            case "keybinds":
                for i in range(10):  AppendToConfig(name, "bindsym", ["$mod+"+str(i), "workspace", "number", str(i)])# Move around workspaces
                for i in range(10):  AppendToConfig(name, "bindsym", ["$mod+Shift+"+str(i), "move", "container", "to", "workspace", "number", str(i)])
                for i in directions: AppendToConfig(name, "bindsym", ["$mod+Shift+"+i, "move", i.lower()])                # Move around windows with directions
                for i in directions: AppendToConfig(name, "bindsym", ["$mod+"+i, "focus", i.lower()])                # Move around windows with directions

                for key, value in Customkeybinds.items(): AppendToConfig(name, "bindsym", [key, *value])
            case "variables":
                for key, value in CustomVars.items():
                    AppendToConfig(name, "set", ['$' + key, value])
            case "general":
                for key, value in CustomGenerals.items(): AppendToConfig(name, key, value)
            case "monitors":
                for key, value in CustomMonitors.items(): AppendToConfig(name, key, value)
            case "execapps":
                os.system("touch " + WORKING_DIR + "/configs/" + name + ".json")
                with open(WORKING_DIR + "/configs/" + name + ".json", "w") as f:
                    f.write(json.dumps(CustomExecApps))
                    f.close()
            case _:
                os.system("touch " + WORKING_DIR + "/configs/" + name + ".json")
                pass
    ReadConfig(name)

def GenerateGenerals(where):
    buffer: str = ""
    with open(where + "/config", "w") as conf:
        # First variables
        print("Setting variables...")
        buffer += "# Sway config generator\n\n# Variables\n"

        for var in variables["set"]: buffer += "set {} {}\n".format(var[0], var[1])
        buffer += "\ninclude {}/*.conf\n".format(WORKING_DIR)

        print("Setting apps...")
        buffer += "\n# Start\n"

        for i in CustomExecApps: buffer += "exec {}\n".format(i)

        print("Setting generals...")
        buffer += "\n# General\n"

        for key, value in general.items():
            buffer += key + (' {\n' if value[0].__len__() else '\n')

            for i in value[0]:
                buffer += '\t'
                for y in i:
                    buffer += y + ' '
                buffer += '\n'

            if value[0].__len__(): buffer += "}\n"

        conf.write(buffer)
        conf.truncate()
def GenerateKeybinds(where):
    buffer: str = ""
    with open(where + "/keybinds.conf", "w") as conf:
        print("Setting keybinds...")
        buffer += "# Keybinds\n"

        buffer += "include {}/config\n\n".format(WORKING_DIR)

        for var in keybinds["bindsym"]:
            buffer += "bindsym"
            for i in var: buffer += (' ' + i)
            buffer += '\n'

        conf.write(buffer)
        conf.truncate()
def GenerateMonitors(where):
    buffer: str = ""
    with open(where + "/monitors.conf", "w") as conf:
        print("Setting monitors...")
        buffer += "# Monitors\n"

        for key, value in monitors.items():
            if value[0]["disable"]:
                buffer += "output {} disable".format(key)
            else:
                buffer += "output {} mode {}Hz position {}\n".format(key, value[0]["mode"], value[0]["position"])
                if not value[0]["scale"] == None:
                    buffer += "output {} scale {}\n".format(key, value[0]["scale"])

        conf.write(buffer)
        conf.truncate()

def ModifyAMonitorMode(name, key, mode, scale = False):
    with open(WORKING_DIR + "/configs/" + name + ".json", "r+") as conf:
        buffer = json.loads(conf.read())

        if not scale:
            match mode:
                case "disable":
                    buffer[key][0]["disable"] = True
                case "toggle":
                    buffer[key][0]["disable"] = not buffer[key][0]["disable"]
                case _:
                    buffer[key][0]["mode"] = mode
        else:
            buffer[key][0]["scale"] = mode

        conf.seek(0)
        json.dump(buffer, conf, indent=4)

        conf.truncate()

MonitorsAvailableModes: dict = {}
default_mode_width: int = 0
default_mode_height: int = 0
default_refresh: int = 0
def ParseMonitors():
    global MonitorsAvailableModes, default_mode_width, default_mode_height, default_refresh
    MonitorsAvailableModes = json.loads(subprocess.run(["swaymsg", "-t", "get_outputs"], capture_output=True, text=True).stdout)
    x = 0
    for monitor in MonitorsAvailableModes:
        default_mode_width = monitor["modes"][0]["width"]
        default_mode_height = monitor["modes"][0]["height"]
        default_refresh = monitor["modes"][0]["refresh"]

        log10 = int(math.log10(default_refresh))
        log10 -= 3 if log10 == 5 else 1

        default_refresh = default_refresh // (10 ** log10)

        CustomMonitors[monitor["name"]] = {
            "mode": str(default_mode_width) + 'x' + str(default_mode_height) + '@' + str(default_refresh), # The last mode from swaymsg
            "position": str(x) + ",0",
            "disable": False,
            "scale": monitor.get("scale")
        }

        # This only works well with two monitors
        if x > 0: x -= (int(default_mode_width) * 2)
        else:     x += int(   default_mode_width   )

if __name__ == "__main__":
    if not os.path.exists(WORKING_DIR + "/configs"):
        os.mkdir(WORKING_DIR + "/configs")

    # First things first, Reading the configs
    variables = ReadConfig("variables")
    keybinds  = ReadConfig("keybinds")
    general   = ReadConfig("general")

    # Parse monitors
    monitors_dict = ParseMonitors()

    monitors = ReadConfig("monitors")
    execapps = ReadConfig("execapps")

    in_use = 0
    for index in range(1, len(sys.argv)):
        if in_use:
            in_use -= 1
            continue

        match sys.argv[index]:
            case "generate-general":
                GenerateGenerals(WORKING_DIR)
                exit(0)
            case "generate-monitors":
                GenerateMonitors(WORKING_DIR)
                exit(0)
            case "generate-keybinds":
                GenerateKeybinds(WORKING_DIR)
                exit(0)
            case "generate-all":
                GenerateGenerals(WORKING_DIR)
                GenerateMonitors(WORKING_DIR)
                GenerateKeybinds(WORKING_DIR)
                exit(0)
            case "reload-sway":
                os.system("swaymsg reload")
                exit(0)
            case "set-monitor-mode":
                if not (sys.argv.__len__() > (index + 2)):
                    sys.stderr.write("Cmd error! set-monitor-mode need at least 2 arguments")
                    exit(1)
                monitor_selected = sys.argv[index + 1]
                resolution_selected = sys.argv[index + 2]

                if resolution_selected == "better":
                    ModifyAMonitorMode("monitors", monitor_selected, "{}x{}@{}".format(default_mode_width, default_mode_height, default_refresh))
                elif not resolution_selected == "toggle":
                    # Check if the selected mode is avaible in sway
                    w = resolution_selected.find('@')
                    s = resolution_selected[:resolution_selected.find('@')].split('x')

                    width  = int(s[0])
                    height = int(s[1])

                    found = False
                    for res in MonitorsAvailableModes[0]["modes"]:
                        if width == res["width"] and height == res["height"]:
                            found = True
                    if not found:
                        sys.stderr.write("Cmd error! that mode isn't available by sway")
                        exit(1)
                else:
                    ModifyAMonitorMode("monitors", monitor_selected, resolution_selected)

                monitors = ReadConfig("monitors")
                GenerateMonitors(WORKING_DIR)

                os.system("swaymsg reload")

                in_use = 2
            case "set-monitor-scale":
                if not (sys.argv.__len__() > (index + 2)):
                    sys.stderr.write("Cmd error! set-monitor-mode need at least 2 arguments")
                    exit(1)
                monitor_selected = sys.argv[index + 1]
                scale_selected = sys.argv[index + 2]

                ModifyAMonitorMode("monitors", monitor_selected, float(scale_selected), True)

                monitors = ReadConfig("monitors")
                GenerateMonitors(WORKING_DIR)

                os.system("swaymsg reload")

                in_use = 2
            case _:
                sys.stderr.write("Cmd error! argument {} wasn't recognized".format(index + 1))
                exit(1)
                pass