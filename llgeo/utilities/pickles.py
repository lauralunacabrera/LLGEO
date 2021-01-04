''' I'm lazy with Pickle files

DESCRIPTION:
This module contains super simple functions that read and write pickle files

FUNCTIONS:
This module contains the following functions:
    * read
    * save
'''
import pickle as pkl

def read(in_path, in_file):
    ''' very simple wrapper for reading pickle files '''

    handler = open(in_path + in_file, 'rb')
    contents = pkl.load(handler)
    handler.close()
    return contents
    
def save(out_path, out_file, contents, flag_save):

    if flag_save:
        handler = open(out_path + out_file, 'wb')
        pkl.dump(contents, handler)
        handler.close()
        print('Pickle file saved at: \n' + out_path + out_file)
    