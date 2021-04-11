import sys
from pathlib import Path
import numpy as np
import pandas as pd
import math
from tqdm import tqdm

import pandas_lightning

from .utils import haversine, calc_xydist
from .quadtree import Point, Rect, QuadTree

# CONSTANTS
REF_MIN_LAT = 1.2203795117581597 # Reference min lat
REF_MIN_LONG = 103.63522841782499 # Reference min long
REF_MAX_LAT = 1.5070712161383 # Reference max lat
REF_MAX_LONG = 104.037804503483 # Reference max long

width, height = calc_xydist(REF_MAX_LONG, REF_MAX_LAT, REF_MIN_LONG,REF_MIN_LAT)
width = math.ceil(width)
height = math.ceil(height)

domain = Rect(width/2, height/2, width, height)

def create_qtree(df, name_col = 'name'):
    qtree = QuadTree(domain, 3)
    points = []
    for index, row in df.iterrows():
        point = Point(row['x'], row['y'], name=row[name_col])

        points.append(point)
        qtree.insert(point)
        
    return qtree, points

def get_x(long):
    x = haversine(long, REF_MIN_LAT, REF_MIN_LONG, REF_MIN_LAT)
    return round(x,2)

def get_y(lat):
    y = haversine(REF_MIN_LONG, lat, REF_MIN_LONG, REF_MIN_LAT)
    return round(y,2)

def get_long_name(a,b):
    return a + '_' + b

def create_amenity_quadtree(path, use_long_name=False):
    raw_data = pd.read_csv(path)

    data = raw_data.copy()

    # qtree = None
    # points = []

    if use_long_name:
        data.lambdas(inplace=True).sapply(
            x = ("lng", get_x),
            y = ("lat", get_y),
            long_name = (["name","type"], get_long_name)
        )
        qtree, points = create_qtree(data, name_col='long_name')
    else:
        data.lambdas(inplace=True).sapply(
            x = ("lng", get_x),
            y = ("lat", get_y),
        )
        qtree, points = create_qtree(data)
    
    return qtree, points

def find_features(qtree, x, y, radius = 3):
    # Count features in 2km, 1km radius, + nearest distance
    # radius = 3
    found_points = []
    qtree.query_radius((x, y), radius, found_points)
    
    count_2km = 0
    count_1km = 0
    nearest_dist = 999
    
    if found_points:
        for p in found_points:
            tmp_dist = np.round(Point(x,y).distance_to(p),2)
            if tmp_dist <= 2.0:
                count_2km += 1
            if tmp_dist <= 1.0:
                count_1km += 1
            if tmp_dist < nearest_dist:
                nearest_dist = tmp_dist

    return count_2km, count_1km, nearest_dist 

def find_features2(row, qtree, radius = 3):
    # print(row)
    # Count features in 2km, 1km radius, + nearest distance
    # radius = 3
    x = row['x']
    y = row['y']

    found_points = []
    qtree.query_radius((x, y), radius, found_points)
    
    count_2km = 0
    count_1km = 0
    nearest_dist = 999
    
    if found_points:
        for p in found_points:
            tmp_dist = np.round(Point(x,y).distance_to(p),2)
            if tmp_dist <= 2.0:
                count_2km += 1
            if tmp_dist <= 1.0:
                count_1km += 1
            if tmp_dist < nearest_dist:
                nearest_dist = tmp_dist

    return pd.Series([count_2km, count_1km, nearest_dist])

def main(filename):

    file_path = Path(filename)
    print(f"Using data file: {file_path}")

    if not file_path.is_file():
        raise FileNotFoundError(f"Data file {filename} not found!")

    ############################################################################
    ############################################################################

    print("Creating amenities Quadtree data ....")
    aux_data_path = Path.cwd() / 'data/auxiliary-data/' 
    
    mrt_qtree, _ = create_amenity_quadtree(aux_data_path / 'sg-train-stations.csv', use_long_name=True)
    prisch_qtree, _ = create_amenity_quadtree(aux_data_path / 'sg-primary-schools.csv')
    secsch_qtree, _ = create_amenity_quadtree(aux_data_path / 'sg-secondary-schools.csv')
    markets_qtree, _ = create_amenity_quadtree(aux_data_path / 'sg-gov-markets-hawker-centres.csv')
    malls_qtree, _ = create_amenity_quadtree(aux_data_path / 'sg-shopping-malls.csv')
    comm_qtree, _ = create_amenity_quadtree(aux_data_path / 'sg-commerical-centres.csv', use_long_name=True)
    
    #  The value in dict is the search radius in km. should be larger for comm due to low quantity
    # Values chosen so as not to get 999 for nearest distance features i.e. nearest amenity not found
    amenities = {
        'mrt':5, 
        'prisch':5, 
        'secsch':5, 
        'markets':10, 
        'malls':3, 
        'comm':10}

    ############################################################################
    ############################################################################

    print("Processing Data ....")
    print("Calc x,y and create empty features")
    
    train_ = pd.read_csv(file_path)
    train = train_[:10].copy(
        
        ).lambdas(inplace=True).sapply(
        x = ("longitude", get_x),
        y = ("latitude", get_y),
        )

    for amenity in amenities:
        train[amenity + '_2km'] = 0
        train[amenity + '_1km'] = 0
        train[amenity + '_ndist'] = None 

    print("Calculating distance features")
    tqdm.pandas(desc="PROGRESS!")

    for amenity in amenities:
        train[[amenity + '_2km', amenity + '_1km', amenity + '_ndist']] = train.progress_apply(find_features2, args=(eval(amenity+'_qtree'), amenities[amenity]), axis=1)

        train = train.astype({
            amenity + '_2km' : 'int32', 
            amenity + '_1km' : 'int32'
        })

    ############################################################################
    ############################################################################
    # Save out results

    out_file_path = file_path.parent / (str(file_path.stem) + '_wdistfeatures' + str(file_path.suffix))
    train.to_csv(out_file_path, index=False)


if __name__ == '__main__':
    
    if len(sys.argv) < 2:
        exit("ERROR! Data file expected: python -m src.create_dist_features [filename]")

    main(sys.argv[1])