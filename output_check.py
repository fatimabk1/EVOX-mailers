import csv
from os import listdir
from os.path import isfile, join


def check(input_file, target_folder):
    success = True
    with open(input_file, 'r') as input:
        reader = csv.DictReader(input)

        expected = []
        for row in reader:
            if row["VIN1"]:
                expected.append(row["VIN1"] + ".jpg")
            if row["VIN2"]:
                expected.append(row["VIN2"] + ".jpg")
            if row["VIN3"]:
                expected.append(row["VIN3"] + ".jpg")

        actual = [img for img in listdir(target_folder) if isfile(join(target_folder, img)) and img != '.DS_Store']
        expected_count = len(expected)
        actual_count = len(actual)

        if(expected_count != actual_count):
            print("IMAGE PRODUCTION FAILURE: {} / {} images produced.".format(actual_count, expected_count))
            success = False
            exit(1)

        expected.sort()
        actual.sort()
        for i in range(actual_count):
            if(actual[i] != expected[i]):
                print("> MISMATCH:", actual[i], " | ", expected[i])
                success = False

    if success:
        print("\n-------------- SUCCESS: {}/{} images match expected output ---------------".format(actual_count, expected_count))
    else:
        print("\n-------------- FAILURE: unexpected or missing image(s) ---------------")

if __name__ == '__main__':
    check()
