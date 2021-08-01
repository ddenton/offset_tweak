import os
import re


def filewalk(root_directory, filetype='ssc'):
    filetype_regex = re.compile(f'.*\.{filetype}')
    for dirpath, dirs, files in os.walk(root_directory):
        # print(f'dirpath={dirpath} dirs={dirs} files={files}')
        for file in files:
            if filetype_regex.match(file):
                print(f'{dirpath}/{file}')


if __name__ == '__main__':
    filewalk('5guys1pack')
