from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os", "sys", "PySimpleGUI",],
                    "excludes": ["tkinter"],
                    "include_files": ['silhouette.jpg']}

# GUI applications require a different base on Windows (the default is for
# a console application).

setup(  name = "evox-downloader",
        version = "0.1",
        description = "EVOX Image Downloader",
        options = {"build_exe": build_exe_options},
        executables = [Executable("gui.py")])
