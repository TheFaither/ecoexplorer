# %%

import pandas as pd
import re

# ---------------------------------------------------------------------------- #
#                                    Finders                                   #
# ---------------------------------------------------------------------------- #


def find_string(filename, target):
    with open(filename, "r") as f:
        for i, line in enumerate(f):
            if target in line:
                return i + 1
    return -1


def findDate(strings, dateformat="%m/%d/%Y"):
    for elem in strings:
        try:
            pd.to_datetime(elem, dateformat)
            return elem
        except Exception:
            return False


def find_equal_pairs(list1, list2):
    equal_pairs = []
    for s1 in list1:
        for s2 in list2:
            if s1 == s2:
                equal_pairs.append(s1)
    return equal_pairs


def filter_strings(files, filter):
    filtered_list = []
    for s1 in files:
        for s2 in filter:
            if s2 in s1:
                filtered_list.append(s1)
                break
    return filtered_list


def extract_text(s : str, start : str, end : str):
    start_index = s.index(start) + len(start)
    end_index = s.index(end, start_index)
    return s[start_index:end_index]



# %%
# ---------------------------------------------------------------------------- #
#                                      txt                                     #
# ---------------------------------------------------------------------------- #
# -------------------------------- functions --------------------------------- #


def extractAttributesAndData(inputfile):
    # -------------------------------- Attributes -------------------------------- #
    attribute = dict()
    # ------------------------------ Test Definition ----------------------------- #
    datatext = extract_text(
        inputfile, '"TestWorks Nano Test Data File"\r\n', "\r\nSegment Definition"
    )
    colsdefin = dict(
        [
            line.replace(" ", "").replace('"', "").split(",")
            for line in datatext.splitlines()
        ]
    )
    attribute.update(colsdefin)
    # ---------------------------- Segment Definition ---------------------------- #
    datatext = extract_text(inputfile, "Segment Definition\r\n", "\r\nEnd")
    colssegmentinverted = [
        line.replace(" ", "").replace('"', "").replace(" ", "").split(",")
        for line in datatext.splitlines()
    ]
    attribute.update({item[1]: item[0] for item in colssegmentinverted})
    # -------------------------------- ID MEASURE -------------------------------- #
    attribute["MeasureID"] = (
        attribute["SampleName"].split(".")[0] + "Test" + str(attribute["TestNumber"])
    )

    # ----------------------------------- Array ---------------------------------- #
    datatext = extract_text(inputfile, '"Channel Data"\r\n', "\r\n\r\n\r\n")
    cols = [
        line.replace('"', "").replace(" ", "").split(",")
        for line in datatext.splitlines()
    ]
    measure = pd.DataFrame(cols)
    measure.columns = measure.iloc[1]
    measure = measure.drop([0, 1, 2])
    measure = measure[~measure.iloc[:, 0].isin([""])]
    for column in measure.columns:
        measure[column] = measure[column].astype("float64")
    # measure.reset_index(inplace=True, drop=True)
    return [attribute, measure]


# ----------------------------------- code ----------------------------------- #
def getattributesandmeasureformultiplefiles(txt_files) -> [list[pd.DataFrame], list]:
    tensile_measures = []
    tensile_attributes = []
    for myfile in txt_files:
        tests = myfile.read().split("Tests ")
        tests_with_data = []
        for index in range(len(tests)):
            test = tests.pop()
            if re.search("Channel Data", test):
                tests_with_data.append(test)
        for test in tests_with_data:
            [tensile_attribute, tensile_measure] = extractAttributesAndData(test)
            tensile_attributes.append(tensile_attribute)
            tensile_measures.append(tensile_measure)
    return [tensile_measures, tensile_attributes]
                

# %%
