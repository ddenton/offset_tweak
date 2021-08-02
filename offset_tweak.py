import fileinput
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


ssc_offset_regex = re.compile('#OFFSET:(.+\.(.+));')


def read_single_file_offset(filepath):
    file = open(filepath, 'r', errors='replace')
    while line := file.readline():
        m = ssc_offset_regex.match(line)
        if m:
            offset, num_decimals = float(m.group(1)), len(m.group(2))
            # print(f'offset={offset} num_decimals={num_decimals}')
            return offset, num_decimals


def read_offsets(df):
    """Read the offsets from the files into the dataframe."""
    for index, row in df.iterrows():
        offset, num_decimals = read_single_file_offset(row['full_filepath'])
        # print(f'offset={offset} num_decimals={num_decimals}')
        df.at[index, 'num_decimals'] = num_decimals
        df.at[index, 'original_offset'] = offset
    return df.astype({'num_decimals': 'int32'})


def write_single_pack_record(df, filepath):
    file = open(filepath, 'w')
    num_decimals = df['num_decimals'].max()
    df2 = df.drop(columns=['full_filepath', 'num_decimals'])
    df2.to_csv(path_or_buf=file, index=False, float_format=f'%.{int(num_decimals)}f')


def apply_single_song_changes(df_row, num_decimals):
    with fileinput.FileInput(df_row['full_filepath'], inplace=True) as file:
        for line in file:
            m = ssc_offset_regex.match(line)
            final_offset = df_row['final_offset']
            if m:
                print(line.replace(m.group(1), f'{final_offset:.{num_decimals}f}'), end='')
            else:
                print(line, end='')


def apply_single_pack_changes(df):
    num_decimals = df['num_decimals'].max()
    for index, row in df.iterrows():
        apply_single_song_changes(row, num_decimals)


def print_single_pack_record_to_console(df, pack_name):
    pack_name = df.at[0, 'pack']
    df2 = df.drop(columns=['pack', 'song', 'full_filepath', 'num_decimals'])
    print(f'Tweaking offsets for \"{pack_name}\"')
    print(df2)


def get_approval_for_single_pack_changes(df):
    if df.shape[0]:
        pack_name = df.at[0, 'pack']
        print_single_pack_record_to_console(df, pack_name)
        while True:
            x = input(f'Apply changes to \"{pack_name}\"? [Y/n] ')
            if "y" == x.lower():
                return True
            elif "n" == x.lower():
                return False


def apply_modification_to_offsets(df, modification):
    df['modification'] = modification
    df['final_offset'] = df['original_offset'] + df['modification']


def get_single_pack_directory(df):
    return os.path.commonpath(df['full_filepath'].tolist())


def filewalk(root_directory, filetype='ssc'):
    """Returns a dataframe with all of the file structure information for files of the requested type."""
    filetype_regex = re.compile(f'.+\.{filetype}')
    df = pd.DataFrame()
    for dirpath, dirs, files in os.walk(root_directory):
        dirs.sort(key=lambda v: v.lower())  # Sort so that we travers in alphabetical depth first order
        # print(f'dirpath={dirpath} dirs={dirs} files={files}')
        for file in files:
            if filetype_regex.match(file):
                splitpath = splitall(dirpath)
                if len(splitpath) == 1:
                    dict = {'pack': None, 'song': splitpath[-1], 'file': file,
                            'full_filepath': os.path.join(dirpath, file)}
                    df = df.append(dict, ignore_index=True)
                else:
                    dict = {'pack': splitpath[-2], 'song': splitpath[-1], 'file': file,
                            'full_filepath': os.path.join(dirpath, file)}
                    df = df.append(dict, ignore_index=True)
    return df


if __name__ == '__main__':
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)
    df = filewalk('5guys1pack')
    df = read_offsets(df)
    apply_modification_to_offsets(df, -0.009)
    if get_approval_for_single_pack_changes(df):
        apply_single_pack_changes(df)
        pack_directory = get_single_pack_directory(df)
        write_single_pack_record(df, os.path.join(pack_directory, 'offset_tweak.csv'))
