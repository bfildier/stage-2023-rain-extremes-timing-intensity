import sys,os,glob
import matplotlib
import matplotlib.pyplot as plt
import sparse
import xarray as xr
import numpy as np
import pandas as pd
from pprint import pprint

import netCDF4
import matplotlib.animation as animation
import imageio
import math
from IPython.display import Video
from tqdm import tqdm
import matplotlib.colors as colors
from matplotlib.colors import LogNorm

from precac_functions import *

# note: variable input must be the same string as found in file names. E.g. precac must be "Precac"

DIR_DATA = "/home/gmaxemin/code/stage-2023-rain-extremes-timing-intensity/input/"

def find_file_with_string(file_list, search_string, start_index, end_index):
    for index, file_name in enumerate(file_list):
        if start_index <= len(file_name) >= end_index and search_string in file_name[start_index:end_index]:
            return index
    
    # Return -1 if the file is not found
    return -1

def get_timestamps(file_list, start_index, end_index):
    found_strings = []
    for file_name in file_list:
        string_found = file_name[start_index:end_index]
        if len(string_found) == (end_index - start_index):
            found_strings.append(string_found)
    return found_strings

def plot_singletime_var(variable: str, timestamp: str):
    print("working")
    
    from matplotlib.colors import LogNorm
    name_dict = {"OM500":"Pressure velocity at 500 mb", "T2mm":"2-m temperature", "OM850":"Pressure velocity at 850 mb", "Precac":"Surface Accum Precip.", "PW":"Precipitable Water", "CWP":"Cloud Water Path", "U10m":"10-m zonal wind", "RH500":"Relative Humidity 500mb", "PSFC":"P at the surface","V10m":"10-m meridional wind","SHF":"Sensible Heat Flux", "LHF":"Latent Heat Flux"}
    unit_dict = {"OM500":"Pa/s","T2mm":"K", "OM850":"Pa/s","Precac":"mm", "PW":"kg/m²", "CWP":"kg/m²", "U10m":"m/s", "RH500":"", "PSFC":"mbar", "V10m":"m/s","SHF":"W/m²", "LHF":"W/m²"}
        
    if variable == "Precac":
        seg_index = timestamp_to_seg_index(timestamp)
        print("i_t:", seg_index)
        df = loadRelTable()
        if seg_index == 0:
            seg_index = 1
        prec = loadPrec(seg_index, df)
        prec_filename = loadPrecacFilename(seg_index, df)

        # Replace negative values with NaN
        prec = xr.where(prec < 0, np.nan, prec)

        variable_data = prec.values
        lon = prec.lon.values
        lat = prec.lat.values
        fig, ax = plt.subplots()

        # Apply logarithmic scaling for positive values
        positive_data = np.where(variable_data > 0, np.log(variable_data), 0)
        # Plot the variable data
        im = plt.imshow(positive_data, origin='lower', extent=[lon.min(), lon.max(), lat.min(), lat.max()], norm=LogNorm(vmin=0.0001)) 

        variable_name = "Surface Accum Precip."

        # Compute vmax based on non-NaN values
        valid_values = positive_data[~np.isnan(positive_data)]
        vmax = np.max(valid_values)
        
    else:
        # Rest of the code...
        matching_files = glob.glob(path_2D + '/*{}*'.format(variable))
        sorted_files = sorted(matching_files)
        i_t = find_file_with_string(sorted_files, timestamp, 119, 129)  # finds index in list of files (119:129 are character indices for time stamp)

        file = sorted_files[i_t]
        dataset = netCDF4.Dataset(file)

        # Getting data
        variable_data = dataset.variables[variable][:]
        # Get the lon and lat values
        lon = dataset.variables['lon'][:]
        lat = dataset.variables['lat'][:]
        # Plot the variable data and assign it to a variable
        fig, ax = plt.subplots()
        im = ax.imshow(variable_data[0, :, :], origin='lower', extent=[lon.min(), lon.max(), lat.min(), lat.max()])

    plt.xlabel('Longitude (° East)')
    plt.ylabel('Latitude (° North)')
    title = f"DYAMOND SAM {name_dict.get(variable)}\nTime Stamp: {timestamp}"
    plt.title(title)
    # ax.grid(True, linestyle='--', linewidth=0.5, color='white', alpha=0.5)
    if variable == "RH500":
        cbar = plt.colorbar(im)  # Use the variable im here to create the colorbar
    else:
        cbar = plt.colorbar(im, label=unit_dict.get(variable))  # Use the variable im here to create the colorbar

    # Show the plot
    plt.show()
    # Return the plot image
    return im

    
def anim_singletime_var(variable: str, timestamps: list = None, desired_duration: int = 20, video_path: str = 'output_video.mp4'):
    # Search for files containing the desired characters
    matching_files = glob.glob(path_2D + '/*{}*'.format(variable))
    sorted_files = sorted(matching_files)

    # Use all available timestamps if none are provided
    if timestamps is None:
        timestamps = get_timestamps(sorted_files, 119, 129)

    # Get the overall minimum and maximum values of variable_data
    min_value = float('inf')
    max_value = float('-inf')

    # Calculate the overall minimum and maximum values
    for timestamp in timestamps:
        i_t = find_file_with_string(sorted_files, timestamp, 119, 129)
        file = sorted_files[i_t]
        dataset = netCDF4.Dataset(file)

        variable_data = dataset.variables[variable][:]
        min_value = min(min_value, variable_data.min())
        max_value = max(max_value, variable_data.max())

    # Create a list to store the frames for the video
    frames = []

    # Generate plots for each timestamp with a progress bar
    with tqdm(total=len(timestamps), desc='Generating Frames') as pbar:
        for timestamp in timestamps:
            i_t = find_file_with_string(sorted_files, timestamp, 119, 129)
            file = sorted_files[i_t]
            dataset = netCDF4.Dataset(file)

            # Getting data
            variable_data = dataset.variables[variable][:]
            # Get the lon and lat values
            lon = dataset.variables['lon'][:]
            lat = dataset.variables['lat'][:]

            # Plot the variable
            fig, ax = plt.subplots()
            img = ax.imshow(variable_data[0, :, :], origin='lower', extent=[lon.min(), lon.max(), lat.min(), lat.max()])
            plt.xlabel('Longitude (° East)')
            plt.ylabel('Latitude (° North)')
            plt.title(f'DYAMOND SAM Precipitable Water\nTime Stamp: {timestamp}')
            ax.grid(True, linestyle='--', linewidth=0.5, color='white', alpha=0.5)
            cbar = plt.colorbar(img, label='Precipitable Water (kg/m²)')

            # Set consistent colorbar limits
            img.set_clim(min_value, max_value)

            # Convert the plot to an image frame
            fig.canvas.draw()
            frame = np.array(fig.canvas.renderer._renderer)
            frames.append(frame)

            plt.close(fig)

            # Update the progress bar
            pbar.set_postfix({'Timestamp': timestamp})
            pbar.update(1)

    # Calculate the desired fps based on the desired duration
    num_frames = len(frames)
    fps = math.ceil(num_frames / desired_duration)

    # Save the frames as a video with the desired fps
    imageio.mimsave(video_path, frames, fps=fps)

    print(f'Video saved to: {video_path}')

def find_file_with_string_df(df, string):
    matching_files = df[df['path_dyamond'].str.contains(string, na=False)]
    file_name = matching_files['path_dyamond'].values[0]
    index = matching_files.index[0]
    return file_name, index    

def timestamp_to_seg_index(timestamp):
    df = loadRelTable()
    file_name, index = find_file_with_string_df(df, timestamp)
    return index
    
