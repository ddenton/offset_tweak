import os
import re

ssc_regex = re.compile('.*\.ssc')


def filewalk(root_directory, regex):
    for dirpath, dirs, files in os.walk(root_directory):
        # print(f'dirpath={dirpath} dirs={dirs} files={files}')
        for file in files:
            if regex.match(file):
                print(f'{dirpath}/{file}')


if __name__ == '__main__':
    filewalk('5guys1pack', ssc_regex)
