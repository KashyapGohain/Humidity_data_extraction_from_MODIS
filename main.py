import geopandas as gpd
import os
import scipy.sparse as sparse
import rasterio
import pandas as pd
import numpy as np
import glob
import gdal
import rasterio.features
import rasterio.warp
from rasterio.crs import CRS


os.chdir('E:/project/modis/data/mod3')
rasterfiles = os.listdir(os.getcwd())
print(rasterfiles)

## Open HDF file
hdflayer = gdal.Open(rasterfiles[0], gdal.GA_ReadOnly)
## Open raster layer
rlayer = gdal.Open(hdflayer.GetSubDatasets()[0][0], gdal.GA_ReadOnly)

# Define output raster and warp-reproject
outputName = rlayer.GetMetadata_Dict()['LOCALGRANULEID'][:-4]+'_LST.tiff'
outputRaster ='E:/project/raster'+outputName
reprj=gdal.Warp(outputRaster,rlayer,dstSRS='EPSG:4326')
print("Data has been projected")
table = pd.DataFrame(index = np.arange(0,1))

# Read the points shapefile using GeoPandas
stations = gpd.read_file(r'E:\project\stations\StationsMOD.shp')
stations['lon'] = stations['geometry'].x
stations['lat'] = stations['geometry'].y

Matrix = pd.DataFrame()
# Iterate through the rasters and save the data as individual arrays to a Matrix
for files in os.listdir(r'E:/project'):
    if files[-5: ] == '.tiff':
        dataset = rasterio.open(r'E:/project'+'\\'+files)
        data_array = dataset.read(1)
        data_array_sparse = sparse.coo_matrix(data_array, shape = (1375,1866))
        data = files[ 6:-5]
        Matrix[data] = data_array_sparse.toarray().tolist()
        print('Processing is done for the image: '+ files[6:-5])

# Iterate through the stations and get the corresponding row and column for the related x, y coordinates
for index, row in stations.iterrows():
    station_name = str(row['Id'])
    lon = float(row['lon'])
    lat = float(row['lat'])
    x, y = (lon, lat)
    row, col = dataset.index(x, y)
    print('Processing: ' + station_name)

    # Pick the rainfall value from each stored raster array and record it into the previously created 'table'
    for records_date in Matrix.columns.tolist():
        a = Matrix[records_date]
        rf_value = a.loc[int(row)][int(col)]
        table[records_date] = rf_value
        transposes_mat = table
        transposes_mat.rename(columns={0: 'LST(k)'}, inplace=True)
        path = r'E:\project\modis\excel'
        transposes_mat.to_csv(path + '\\' + station_name + '.csv')

    filenames = glob.glob(path + "/*.csv")
    print(filenames)
    dfs = []

df = pd.concat([pd.read_csv(fp).assign(New=os.path.basename(fp).split('.')[0]) for fp in filenames],ignore_index=True,sort=True)
print (df)
df.to_csv(path+"\\"+'marge_ST.csv', index=True)
print("processing completed")
