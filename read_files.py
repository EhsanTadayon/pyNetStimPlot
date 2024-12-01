import pandas as pd
import os
def read_foci_file(filepath):
    """
    reads a foci file

    :param:
    filepath: path to the foci file

    :return:
    return the pandas dataframe or return appropriate exceptions
    """
    # check extension and raise error if it is not .csv
    #extension = os.path.splitext(filepath)[1]
    #if extension!='.csv':
        #raise NotCSVFile(filepath)

        # read the csv file and check the x,y,z columns are available
    df = pd.read_csv(filepath)
    for col in ['x','y','z']:
        if col not in df.columns:
            raise RequiredColumnsNotAvailable(col)
    return df



class RequiredColumnsNotAvailable(KeyError):
    pass

class NotCSVFile(TypeError):
    pass
