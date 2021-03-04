import csv
from os import listdir
from os.path import isfile, join

with open('data.csv', 'r') as input:
    reader = csv.DictReader(input)

    expected = []
    for row in reader:
        name = row["vin"] + ".jpg"
    
    actual = [img for img in listdir("images/") if isfile(join("images/", img))]

    expected.sort()
    actual.sort()
    assert(len(expected) == len(actual))
    num = len(expected)

    for i in range(num):
        assert(expected[i] == actual[i])
    input.close()

print("All data successfully converted to images!")
