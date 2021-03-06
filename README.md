# offset_tweak
A simple tool for changing stepmania songs between the ITG offset and null offset.

#### Requirements
offset_tweak.py is a single script requiring Python3 and Pandas. Installing [Anaconda](https://www.anaconda.com/products/individual) would be my recommended approach.

#### Usage
The script should be run with two arguments. The first argument can be either `--toitg` (+0.009) or `--tonull` (-0.009) or `--reset`. The second argument is the root_directory from which the script should begin its search. This path can be either relative or absolute, and it should point either to a single song-pack which you wish to convert, or to a parent directory of one or more song-packs which can all be converted together. (Note that you will be asked to confirm the conversion of each pack individually, so it is fine to point to your `Song` directory when only a subset of your packs need conversion.)

###### Example 
```
$ python offset_tweak.py --tonull 'Songs/Rainbow Locus'
```

The program will run pack by pack. For each song-pack that it finds, it will list the proposed offset changes to be made to that pack's .ssc and .sm files. No changes will be applied unless the user accepts. If the user does accept, then edits will be made to the files' offsets, and a csv file named `offset_tweak.csv` will be written to the song-pack directory detailing the initial and final offsets for each song. 

Regardless of whether the user accepts, the script will then proceed to the next song-pack.

###### Example 
```
Tweaking offsets for "5guys1pack"
                                                 file  initial_offset  modification  final_offset
0                                          Addict.ssc          -0.647        -0.009        -0.656
1                                            Aiwa.ssc           0.009        -0.009         0.000
2    Black Tiger Sex Machine & Lektrique - Armada.ssc           0.009        -0.009         0.000
3                                 Armada SK remix.ssc           0.009        -0.009         0.000
4                                     Beat Dem Up.ssc           0.009        -0.009         0.000
5                               Came to Get Funky.ssc           0.008        -0.009        -0.001
6                               Caught Red Handed.ssc          -0.141        -0.009        -0.150
7                  Dance with Cannibals (Auratic).ssc           0.095        -0.009         0.086
8                                        Dissaray.ssc           0.009        -0.009         0.000
9                Bioblitz & Wildpuppet - Dog Days.ssc           0.009        -0.009         0.000
10                                   Doppelganger.ssc           0.005        -0.009        -0.004
11                           Dropgun - Earthquake.ssc           0.009        -0.009         0.000
12              ECHO (The Living Tombstone Remix).ssc           0.010        -0.009         0.001
13                                   Fuck Gravity.ssc          -0.018        -0.009        -0.027
14                                      G41 Theme.ssc          -0.527        -0.009        -0.536
15                              ganggangplanklmao.ssc          -0.661        -0.009        -0.670
16  Secret Weapons - Ghost (Tommie Sunshine & SLAT...           0.009        -0.009         0.000
Apply changes to "5guys1pack"? [Y/n] 
```
#### Record Keeping and Idempotency

The `offset_tweak.csv` file stored in each song-pack directory is used by tweak to keep track of already applied changes. Thus, running with `--toitg` multiple times will ignore any packs that have already had the appropriate offset mod aplied. Similarly, running with `--reset` will return all the songs to their initial offset before deleting the `offset_tweak.csv`.

#### Custom Offsets

Optionaly, tweak now accepts a custom offset as a substitute for the fixed offset options (toitg or tonull). Example usage:
```
$ python offset_tweak.py --custom -0.010 'Songs/Rainbow Locus'
```


#### File Encodings

In testing, I have discovered that some `.ssc` and `.sm` files use the ISO-8859-1 encoding instead of utf-8. offset_tweak.py now accepts these ISO-8859-1 encoded files, but if it makes any changes it will resave the files as utf-8. (This shouldn't be problematic as transcoding from ISO-8859-1 to utf-8 is lossless.)

