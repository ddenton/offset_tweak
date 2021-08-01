import os
import re
import pandas as pd


def splitall(path):
    """Split the path into all of its parts.

    Credit: Trent Mick, O'Reilly Python Cookbook
    """
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path:  # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def filewalk(root_directory, filetype='ssc'):
    """Returns a dataframe with all of the file structure information for files of the requested type."""
    filetype_regex = re.compile(f'.+\.{filetype}')
    df = pd.DataFrame()
    for dirpath, dirs, files in os.walk(root_directory):
        # print(f'dirpath={dirpath} dirs={dirs} files={files}')
        for file in files:
            if filetype_regex.match(file):
                splitpath = splitall(dirpath)
                if len(splitpath) == 1:
                    dict = {'pack': None, 'song': splitpath[-1], 'file': file, 'full_filepath': os.path.join(dirpath, file)}
                    df = df.append(dict, ignore_index=True)
                else:
                    dict = {'pack': splitpath[-2], 'song': splitpath[-1], 'file': file, 'full_filepath': os.path.join(dirpath, file)}
                    df = df.append(dict, ignore_index=True)
    return df


if __name__ == '__main__':
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)
    df = filewalk('5guys1pack')
    print(df)
