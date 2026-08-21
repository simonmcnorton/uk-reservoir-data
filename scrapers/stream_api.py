import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Default or placeholder ArcGIS FeatureServer Layer URL
DEFAULT_ARCGIS_URL = "https://services.arcgis.com/your-service/FeatureServer/0"


def fetch_stream_reservoir_data(arcgis_url: str = DEFAULT_ARCGIS_URL) -> Dict[str, Dict[str, Any]]:
    """
    Fetch reservoir data from a generic ArcGIS FeatureServer / MapServer REST endpoint.
    Constructs the query: <url>/query?where=1=1&outFields=*&f=json
    
    Args:
        arcgis_url: Base URL to the ArcGIS FeatureServer or MapServer layer.
        
    Returns:
        Dictionary mapping reservoir name to its capacity percentage and metadata:
        {
            "Reservoir Name": {
                "percentage": float,
                "timestamp": str,
                "latitude": Optional[float],
                "longitude": Optional[float],
                "attributes": dict
            }
        }
    """
    reservoir_data: Dict[str, Dict[str, Any]] = {}
    
    # Ensure clean endpoint path
    base_endpoint = arcgis_url.rstrip('/')
    query_url = f"{base_endpoint}/query"
    
    params = {
        'where': '1=1',
        'outFields': '*',
        'f': 'json',
        'returnGeometry': 'false'
    }
    
    headers = {
        'User-Agent': 'UK-Reservoir-Monitor/1.0 (Data-Pipeline; ArcGIS-REST-Client)',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(query_url, params=params, headers=headers, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for ArcGIS API error response
        if 'error' in data:
            error_details = data['error']
            print(f"ArcGIS REST Error {error_details.get('code')}: {error_details.get('message')}")
            return {}
            
        features = data.get('features', [])
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        for feature in features:
            attributes = feature.get('attributes', {})
            if not attributes:
                continue
            
            # 1. Extract Reservoir Name (case-insensitive fallback check)
            reservoir_name = None
            name_candidate_keys = [
                'name', 'reservoir_name', 'Reservoir', 'RESERVOIR_NAME',
                'SITE_NAME', 'SiteName', 'site_name', 'Location', 'location',
                'asset_name', 'AssetName'
            ]
            
            for key in name_candidate_keys:
                if key in attributes and attributes[key]:
                    reservoir_name = str(attributes[key]).strip()
                    break
            
            # Fallback: case-insensitive search through all attributes
            if not reservoir_name:
                for k, v in attributes.items():
                    if any(sub in k.lower() for sub in ['name', 'reservoir', 'site']) and v:
                        reservoir_name = str(v).strip()
                        break
            
            # 2. Extract Capacity Percentage
            raw_percentage = None
            pct_candidate_keys = [
                'capacity_percentage', 'percentage', 'level', 'percent_full',
                'PERCENTAGE', 'CAPACITY_PERCENTAGE', 'PERCENT_FULL',
                'storage_pct', 'STORAGE_PCT', 'curr_capacity_pct', 'pct_storage'
            ]
            
            for key in pct_candidate_keys:
                if key in attributes and attributes[key] is not None:
                    raw_percentage = attributes[key]
                    break
            
            # Fallback: case-insensitive search for percentage fields
            if raw_percentage is None:
                for k, v in attributes.items():
                    if any(sub in k.lower() for sub in ['percent', 'capacity', 'level', 'pct', 'storage']) and v is not None:
                        raw_percentage = v
                        break
            
            if reservoir_name and raw_percentage is not None:
                try:
                    # Clean strings like "85.2%" or decimal fractions (0.852 -> 85.2)
                    if isinstance(raw_percentage, str):
                        clean_pct_str = raw_percentage.replace('%', '').strip()
                        capacity_percentage = float(clean_pct_str)
                    else:
                        capacity_percentage = float(raw_percentage)
                    
                    # If expressed as a 0.0 - 1.0 fraction
                    if 0.0 < capacity_percentage <= 1.0:
                        capacity_percentage = round(capacity_percentage * 100, 2)
                    else:
                        capacity_percentage = round(capacity_percentage, 2)
                        
                except (ValueError, TypeError):
                    continue
                
                # Optional coordinates from attributes if present
                lat = attributes.get('latitude') or attributes.get('LATITUDE') or attributes.get('lat')
                lng = attributes.get('longitude') or attributes.get('LONGITUDE') or attributes.get('lon') or attributes.get('lng')
                
                reservoir_data[reservoir_name] = {
                    "percentage": capacity_percentage,
                    "timestamp": current_time,
                    "latitude": float(lat) if lat is not None else None,
                    "longitude": float(lng) if lng is not None else None,
                    "attributes": attributes
                }
        
        print(f"Extracted {len(reservoir_data)} reservoir entries from Stream ArcGIS API")
        return reservoir_data
        
    except requests.RequestException as e:
        print(f"Network error querying Stream ArcGIS API: {e}")
        return {}
    except Exception as e:
        print(f"Unexpected error processing Stream ArcGIS API data: {e}")
        return {}


def fetch_reservoir_levels(arcgis_url: str = DEFAULT_ARCGIS_URL) -> Dict[str, Dict[str, Any]]:
    """
    Main entrypoint called by aggregator pipelines.
    Returns:
        { reservoir_name: { "percentage": float, "timestamp": str, ... } }
    """
    return fetch_stream_reservoir_data(arcgis_url=arcgis_url)