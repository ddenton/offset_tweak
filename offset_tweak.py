import errno
import getopt
import os
import re
import sys

import numpy as np
import pandas as pd


def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occurred


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


offset_regex = re.compile('#OFFSET:(.+\.(.+));')


def read_single_file_offset(filepath):
    with open(filepath, 'r', errors='replace') as f:
        while line := f.readline():
            m = offset_regex.match(line)
            if m:
                offset, num_decimals = float(m.group(1)), len(m.group(2))
                # print(f'offset={offset} num_decimals={num_decimals}')
                return offset, num_decimals


def read_current_offsets(df):
    """Read the current offsets and use these as the initial offsets whenever we failed to get them from a record."""
    for index, row in df.iterrows():
        offset, num_decimals = read_single_file_offset(row['full_filepath'])
        # print(f'offset={offset} num_decimals={num_decimals}')
        df.at[index, 'current_offset'] = offset
        if pd.isnull(row['initial_offset']):
            df.at[index, 'num_decimals'] = num_decimals
            df.at[index, 'initial_offset'] = offset
    return df


def write_single_pack_record(df, filepath):
    with open(filepath, 'w') as file:
        num_decimals = df['num_decimals'].max()
        df2 = df.drop(columns=['full_filepath', 'num_decimals', 'current_offset'])
        df2.to_csv(path_or_buf=file, index=False, float_format=f'%.{int(num_decimals)}f')


def read_single_pack_record(df, filepath):
    """ Read the initial_offsets into the dataframe from the offset_tweak.csv record if it exists."""
    try:
        with open(filepath, 'r') as file:
            df2 = pd.read_csv(filepath)
            for index, row in df2.iterrows():
                df.loc[(df['pack'] == row['pack']) &
                       (df['song'] == row['song']) &
                       (df['file'] == row['file']), 'initial_offset'] = row['initial_offset']
                df.loc[(df['pack'] == row['pack']) &
                       (df['song'] == row['song']) &
                       (df['file'] == row['file']), 'num_decimals'] = 6
        return True
    except FileNotFoundError:
        return False


offset_regex_outer_group = re.compile('(#OFFSET:.+\..+;)')


def replace_offset(str, final_offset, num_decimals):
    if offset_regex_outer_group.match(str):
        return f'#OFFSET:{final_offset:.{num_decimals}f};'
    return str


def apply_single_song_changes_with_encoding(full_filepath, final_offset, num_decimals, input_encoding,
                                            output_encoding='utf-8'):
    with open(full_filepath, 'r', encoding=input_encoding) as f:
        content = f.read()
    replaced = (replace_offset(s, final_offset, num_decimals) for
                s in re.split(offset_regex_outer_group.pattern, content))
    content = (''.join(replaced)).encode(output_encoding)
    with open(full_filepath, 'wb') as o:
        o.write(content)


def apply_single_song_changes(df_row, num_decimals):
    full_filepath = df_row['full_filepath']
    final_offset = df_row['final_offset']
    encoding, output_encoding = 'utf-8', 'utf-8'
    try:
        apply_single_song_changes_with_encoding(full_filepath, final_offset, num_decimals, encoding,
                                                output_encoding=output_encoding)
    except UnicodeDecodeError as e:
        try:
            encoding = 'ISO-8859-1'
            apply_single_song_changes_with_encoding(full_filepath, final_offset, num_decimals, encoding,
                                                    output_encoding=output_encoding)
            print(f'Detected {encoding} encoding for {full_filepath}, re-encoded as {output_encoding}')
        except:
            raise  # If neither of the supported encoding types worked, THEN throw the exceptions


def apply_single_pack_changes(df):
    num_decimals = df['num_decimals'].max()
    for index, row in df.iterrows():
        apply_single_song_changes(row, num_decimals)


def print_single_pack_record_to_console(df, pack_name):
    df2 = df.drop(columns=['pack', 'song', 'full_filepath', 'num_decimals', 'current_offset'])
    print(f'Tweaking offsets for \"{pack_name}\"')
    print(df2)


def no_change_slice(df):
    return [not np.isclose(current_offset, final_offset) for
            current_offset, final_offset in zip(df['current_offset'], df['final_offset'])]


def get_approval_for_single_pack_changes(df):
    pack_name = None
    if df.shape[0]:
        pack_name = df.at[0, 'pack']
    df = df.loc[no_change_slice, :]
    if df.shape[0]:
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


def filewalk(root_directory, filetypes=('ssc', 'sm')):
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
    pd.set_option('display.max_rows', None)

    df = filewalk(root_directory)
    if df.empty:
        print(f'No songs found at root_directory={root_directory}"')
    else:
        df = df.assign(num_decimals=np.NaN)
        df = df.assign(initial_offset=np.NaN)
        for pack, pack_df in df.groupby('pack'):
            pack_directory = get_single_pack_directory(pack_df)
            read_single_pack_record(df, os.path.join(pack_directory, 'offset_tweak.csv'))
        df = read_current_offsets(df)
        df = df.astype({'num_decimals': 'int32'})

        apply_modification_to_offsets(df, modification)

        for pack, pack_df in df.groupby('pack'):
            pack_df = pack_df.copy().reset_index(drop=True)
            if get_approval_for_single_pack_changes(pack_df):
                apply_single_pack_changes(pack_df)
                pack_directory = get_single_pack_directory(pack_df)
                if modification:
                    write_single_pack_record(pack_df, os.path.join(pack_directory, 'offset_tweak.csv'))
                else:
                    silentremove(os.path.join(pack_directory, 'offset_tweak.csv'))



def main(argv):
    help_string = 'offset_tweak.py {--toitg | --tonull | --reset} <root_directory>'

    modification = 0.0
    try:
        opts, args = getopt.getopt(argv, "h", ["help", "toitg", "tonull", "reset", "custom="])
    except getopt.GetoptError:
        print(help_string)
        sys.exit(2)
    for opt, arg in opts:
        if opt == ('-h', '--help'):
            print(help_string)
            sys.exit()
        elif opt == '--toitg':
            modification = 0.009
        elif opt == '--tonull':
            modification = -0.009
        elif opt == '--reset':
            modification = 0.0
        elif opt == '--custom':
            modification = float(arg)
    if len(args) != 1:
        print(help_string)
        sys.exit(2)
    else:
        tweak_offsets(args[0], modification)


if __name__ == "__main__":
    main(sys.argv[1:])
