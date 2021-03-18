import csv
import traceback
import PySimpleGUI as sg
import os
import main
import time
import sys

sg.theme('Dark Blue 3')

# Tab view

# Run Program - Tab 1
# mytext = "hello\nthere\nmy\ndear\nfriend\n!"
resolution_choices = ['320', '480', '640', '1280', '2400']
layout = [
    [sg.Text('Upload a .csv file', size=(50,2)),
        sg.FileBrowse(key='--DATA--', file_types=("CSV Files", "*.csv"))],
    [sg.Text('Select an image resolution', size=(50,1)), 
        sg.InputCombo(resolution_choices, key='--RESOLUTION--', default_value=[resolution_choices[0]])],
    [sg.Text("Select target folder for image downloads", size=(50,2)),
        sg.FolderBrowse(key='--DOWNLOAD--')],
    [sg.Submit(), sg.Cancel()],
    [sg.Output(size=(100,20))]]


window = sg.Window('EVOX Image Downloader', layout, font=("Helvetica", 15), size=(700, 500))
# window.AddRow()
print('\n\n\n\n')
    # check for event


# handle event
# while True:
event, values = window.read()
if event == "Cancel" or event == sg.WIN_CLOSED or event == "Exit":
    window.close()
elif event == "Submit":
    # validate and save input file
    path = values['--DATA--']
    print("Input File:", path)
    resolution = values['--RESOLUTION--']
    print("Resolution:", resolution)
    target_folder = values['--DOWNLOAD--']
    print("Target Folder:", target_folder)
    name, extension = os.path.splitext(path)
    if extension != ".csv":
        sg.PopupError("Please submit a .CSV file")
        window.close()
    else:
        print("\n"*2)
        print("\t\t------NOTES-----")
        print("> The download program has officialy started -- interface will be unresponsive until completion. Scroll will be available to view program output upon conclusion.")
        print("> All files will be saved saved in target folder.")
        print("> Images are saved in target_folder/images{date}{time}; Logs are saved in target_folder/logs{date}{time}")
        print("> Please wait patiently. Process may take up to five minutes to complete.\n\n")
        print("*\n"*2)
        main.run(path, target_folder, resolution)
        sg.popup('All downloads complete!')


event, values = window.read()
if event:
    window.close()
    sys.exit(0)
