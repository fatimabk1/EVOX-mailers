import csv
import PySimpleGUI as sg
import os
import main
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
    [sg.Submit(),
        sg.Cancel()]]

print(sys.stderr)

window = sg.Window('EVOX Image Downloader', layout, font=("Helvetica", 15), size=(700, 500))
# window.AddRow(sg.Output(size=(100,20)))
print('\n\n\n\n')
    # check for event
event, values = window.read()

# handle event
if event == "Cancel" or event == sg.WIN_CLOSED:
    window.close()
elif event == "Submit":
    # validate and save input file
    path = values['--DATA--']
    print("path:", path)
    resolution = values['--RESOLUTION--']
    print("resolution:", path)
    target_folder = values['--DOWNLOAD--']
    print("download:", path)

    name, extension = os.path.splitext(path)
    if extension != ".csv":
        sg.Popup("ERROR: please submit a .CSV file")
        window.close()
    else:
        with open(path, 'r') as upload, open('input.txt', 'w') as save_file:
            save_file.write(upload.read())
        resolution = values['Resolution']
        main.run('input.txt', target_folder, resolution)
        sg.popup('All downloads complete!')
