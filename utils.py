import numpy as np
import pandas as pd



def get_elec_name(channel):
    if channel[-1] in [str(i) for i in range(0,10)]:
        return get_elec_name(channel[:-1])
    else:
        return channel


def generate_diverging_electrode_colors(electrodes):
    """
    Generates a unique diverging color for each class.

    Parameters:
    num_classes (int): The number of different classes.

    Returns:
    list: A list of RGB tuples representing the colors.
    """
    # Use the seaborn diverging color palette
    palette = sns.color_palette("Spectral", len(electrodes))
    results = {elec: p for elec, p in zip(electrodes, palette)}
    return results


def parse_elec_file(elec_file):
    df = pd.read_csv(elec_file)

    # check the columns are provided
    needed_cols = ['channel','x','y','z']
    optional_cols = ['color','scale_factor','opacity']

    for col in needed_cols:
        assert col in df.columns,f'{col} was not found in the table.'

    # add electrode names to the dataframe
    df['elec'] = df.channel.apply(lambda x: get_elec_name(x))

    #color
    if 'color' not in df.columns:
        elec_colors = generate_diverging_electrode_colors(np.unique(df.elec.to_numpy()))
        df['color'] = df.elec.apply(lambda x: elec_colors[x])

    if 'scale_factor' not in df.columns:
        df['scale_factor'] = [1] * df.shape[0]

    if 'opacity' not in df.columns:
        df['opacity'] = [1] * df.shape[0]

    return df

