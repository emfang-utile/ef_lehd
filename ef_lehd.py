import pandas as pd
import geopandas as gpd
import numpy as np
import requests
import json
import os
from shapely.geometry import GeometryCollection, Polygon, MultiPolygon
from shapely.validation import make_valid

def get_sum_within_boundary(trip_dot, boundary, boundary_type, direction):
    
    #Ensure data and boundary have the same crs.
    boundary = boundary.to_crs(trip_dot.crs)

    #Join data to boundary so that every instance of data has boundary attached.
    joined = gpd.sjoin(trip_dot, boundary, how="inner", predicate="within")

    #Count number of data within each boundary.
    trips_per_bound = joined.groupby("NAME")[f"tot_jobs"].size().reset_index()

    #Rename 'tot_jobs' to include direction traveled.
    #jobs_direction = f"tot_jobs_{direction}"
    trips_per_bound = trips_per_bound.rename(columns={'tot_jobs' : f"tot_jobs_{direction}"})

    #Add new column called 'bound_type'
    trips_per_bound['bound_type'] = boundary_type

    return trips_per_bound

def extract_polygons(geometry):
    if isinstance(geometry, GeometryCollection):
        print("Found a Geometry Collection.")

        # Count number of polygons in the Geometry Collection
        polygons = ([g for g in geometry.geoms if isinstance(g, (Polygon, MultiPolygon))])
        print(f"This Geometry Collection has {len(polygons)} polygons.")
        
        #Case 1: there are no polygons in the Geometry Collection
        if not polygons:
            return None
        
        # Case 2: there are multiple polygons in the Geometry Collection (make into a MultiPolygon)
        elif len(polygons) > 1:
            print(f"Combined {len(polygons)} polygons into a MultiPolygon.")
            return MultiPolygon(polygons)
        
        # Case 3: there is exactly one polygon in the Geometry Collection
        else:
            return polygons[0]
    else:
        return geometry
    
def get_blocks_for_dot(lehd_gdf, layers, output_name):
    lehd_gdf.to_file("test.gpkg", driver="GPKG")
    print("save to file works within this function")
    # Initialize gdf_for_dots
    gdf_for_dots = lehd_gdf
    
    for lyr, details in layers.items():
        # Convert layer to the same CRS as lehd_data
        lyr_gdf = details['data']
        lyr_gdf = lyr_gdf.to_crs(lehd_gdf.crs)
        print("Converted layer crs to match lehd_data")

        # Check for invalid geometries
        num_invalid = len(lyr_gdf[lyr_gdf['geometry'].is_valid == False])
        
        # No invalid geometries
        if num_invalid == 0:
            print(f"There were no invalid geometries found in {lyr}.")
        
        # Invalid geometries found
        else:
            print(f"Found {num_invalid} invalid geometries in {lyr}.")
            
            # Try basic buffer(0) fix invalid geometries
            lyr_gdf['geometry'] = lyr_gdf['geometry'].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)
        
            # Try make_valid to fix invalid geometries
            lyr_gdf['geometry'] = lyr_gdf['geometry'].apply(lambda geom: make_valid(geom) if not geom.is_valid else geom)
        
            num_invalid = len(lyr_gdf[lyr_gdf['geometry'].is_valid == False])
            if num_invalid == 0:
                print(f"Fixed all invalid geometries in {lyr}.")
            else:
                print(f"After trying geom.buffer(0) and make_valid(geom), there are still {num_invalid} invalid geometries in {lyr}.")

        # Get features in layers that intersect with LEHD blocks
        print(f"Finding features in {lyr} that intersect with LEHD data...")
        lyr_gdf_joined = gpd.sjoin(lyr_gdf, lehd_gdf, how = "inner", predicate="intersects").reset_index()
        lyr_gdf_joined = lyr_gdf_joined[lyr_gdf_joined.columns]

        # Clip lehd_gdf by lyrs
        if details['operation'] == "clip":
            print(f"Clipping LEHD data by {lyr}...")
            gdf_for_dots = gdf_for_dots.clip(lyr_gdf_joined)
            print(f"Successfully clipped LEHD data by {lyr}.")

        # Difference lehd_gdf by lyrs
        elif details['operation'] == "difference":
            gdf_for_dots['geometry'] = gdf_for_dots['geometry'].difference(lyr_gdf_joined.union_all())
            print(f"Successfully found difference between LEHD data and {lyr}")

        else:
            print("Not a valid operation. Operation should be 'clip' or 'difference'.")

    # Check for geometry collections - If there are geometry collections, only keep the polygons
    print("Extracting polygons from Geometry Collections...")
    gdf_for_dots["geometry"] = gdf_for_dots["geometry"].apply(extract_polygons)
    gdf_for_dots = gdf_for_dots[gdf_for_dots["geometry"].notnull()]
    print("Sucessfully extracted polygons from Geometry Collections.")

    # Export layer
    gdf_for_dots.to_file(f"output/{output_name}.gpkg", driver="GPKG")

    return gdf_for_dots
