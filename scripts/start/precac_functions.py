import xarray as xr
import gc,os
import pandas as pd

#-- Paths

# DIR_DYAMOND (where DYAMOND data are)

path_DYAMOND_REGIONS = '/data/bfildier/DYAMOND_REGIONS/'
path_reg1_SAM = os.path.join(path_DYAMOND_REGIONS, "130E_165E_0N_20N/SAM")
path_2D = os.path.join(path_reg1_SAM,'2D')

DIR_DYAMOND = path_2D
print(DIR_DYAMOND)

# DIR_DATA (where segmentation relation table is)

DIR_DATA = "/home/gmaxemin/code/stage-2023-rain-extremes-timing-intensity/input/"

#-- Functions

def loadPrecac(i_t,df):
    
    root = df.iloc[i_t]['path_dyamond']
    file_precac = str(root) + '.Precac.2D.nc'
    # load
    precac = xr.open_dataarray(os.path.join(DIR_DYAMOND, file_precac), engine='netcdf4').load()[0]
    # precac = xr.open_dataarray(os.path.join(DIR_DYAMOND,file_precac)).load()[0]
    
    return precac


def loadPrecacFilename(i_t,df):
    
    root = df.iloc[i_t]['path_dyamond']
    file_precac = str(root) + '.Precac.2D.nc'
    filename = os.path.join(DIR_DYAMOND,file_precac)

    return filename


def loadPrec(i_t,df):
    
    # Load DYAMOND-SAM Precac
    precac_prev = loadPrecac(i_t-1,df)
    precac_current = loadPrecac(i_t,df)
    
    # get 30mn precipitation from difference
    prec = precac_current - precac_prev
    
    # free up memory
    del precac_prev
    del precac_current
    gc.collect()
    
    return prec

def loadPref_nc_file(i_t,df):
    prec = loadPrec(i_t,df)
    
    # i_t to timestamp
    file_name = df.loc[i_t, 'path_dyamond']
    timestamp = file_name[119:129]
    print(timestamp)
    
    # Specify the output file path and name
    output_file = f"DYAMOND_9216x4608x74_7.5s_4km_4608_{timestamp}.Prec_calculated.2D.nc"

    # Save the 'prec' DataArray as a NetCDF file
    prec.to_netcdf(output_file, format="NETCDF4")

def loadRelTable(which='DYAMOND_SEG'):
    
    # relation table DYAMOND-SAM -- TOOCAN segmentation masks
    if which == 'DYAMOND_SEG':
        df = pd.read_csv(os.path.join(DIR_DATA,'relation_2_table_UTC_dyamond_segmentation.csv'))
        df.sort_values(by='UTC',ignore_index=True,inplace=True)

    return df