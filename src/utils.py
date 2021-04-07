from math import radians, cos, sin, asin, sqrt
import numpy as np

def haversine(lon1, lat1, lon2, lat2):
    """Calculate the distance in km between 2 geograhical coordinates

    Parameters
    ----------
    lon1 : float
        Longitude of the first point
    lat1 : float
        Latitude of the second point
    lon2 : float
        Longitude of the second point
    lat2 : float
        Latitude of the second point

    Returns
    -------
    float
        Distance in km
    """    

    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    # lon1 = radians(lon1)
    # lon2 = radians(lon2)
    # lat1 = radians(lat1)
    # lat2 = radians(lat2)

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = np.sin(dlat/2)**2 + np.cos(lat1) * cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def calc_xydist(lon1, lat1, lon2, lat2):
    """Calculate the orthogonal x and y distances in km between 2 geographical coordinates

    Parameters
    ----------
    lon1 : float
        Longitude of the first point
    lat1 : float
        Latitude of the second point
    lon2 : float
        Longitude of the second point
    lat2 : float
        Latitude of the second point

    Returns
    -------
    float
        x and y distances in km
    """    

    x_dist = haversine(lon1, lat1, lon2, lat1)
    y_dist = haversine(lon1, lat1, lon1, lat2)

    return x_dist, y_dist

