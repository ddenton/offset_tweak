import fileinput
import getopt
import os
import re
import sys

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
        df.at[index, 'initial_offset'] = offset
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
    df['final_offset'] = df['initial_offset'] + df['modification']


def get_single_pack_directory(df):
    return os.path.commonpath(df['full_filepath'].tolist())


def filewalk(root_directory, filetypes=['ssc', 'sm']):
    """Returns a dataframe with all of the file structure information for files of the requested type."""
    combined_filetypes = '|'
    combined_filetypes = combined_filetypes.join(filetypes)
    filetype_regex = re.compile(f'.+\.({combined_filetypes})')
    df = pd.DataFrame()
    valid_root_directory = False
    for dirpath, dirs, files in os.walk(root_directory):
        dirs.sort(key=lambda v: v.lower())  # Sort so that we travers in alphabetical depth first order
        files.sort(key=lambda v: v.lower())  # Sort so that we travers in alphabetical depth first order
        # print(f'dirpath={dirpath} dirs={dirs} files={files}')
        valid_root_directory = True
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
    if not valid_root_directory:
        raise ValueError(f'Invalid root_directory={root_directory}')
    return df


def tweak_offsets(root_directory, modification):
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

    df = filewalk(root_directory)
    if df.empty:
        print(f'No songs found at root_directory={root_directory}"')
    else:
        df = read_offsets(df)
        apply_modification_to_offsets(df, modification)

        for pack, pack_df in df.groupby('pack'):
            pack_df = pack_df.copy().reset_index(drop=True)
            if get_approval_for_single_pack_changes(pack_df):
                apply_single_pack_changes(pack_df)
                pack_directory = get_single_pack_directory(pack_df)
                write_single_pack_record(pack_df, os.path.join(pack_directory, 'offset_tweak.csv'))


def main(argv):
    help_string = 'offset_tweak.py {--toitg | --tonull} <root_directory>'

    modification = 0.0
    try:
        opts, args = getopt.getopt(argv, "h", ["toitg", "tonull"])
    except getopt.GetoptError:
        print(help_string)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(help_string)
            sys.exit()
        elif opt == '--toitg':
            modification = 0.009
        elif opt == '--tonull':
            modification = -0.009
    if len(args) != 1:
        print(help_string)
        sys.exit(2)
    else:
        tweak_offsets(args[0], modification)


if __name__ == "__main__":
    main(sys.argv[1:])
