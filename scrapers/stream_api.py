import requests
from datetime import datetime, timezone

def fetch_stream_reservoir_data():
    """
    Fetch reservoir data from Stream Open Data Hub using ArcGIS REST API.
    Uses the ArcGIS Feature Server format: url + /query?where=1=1&outFields=*&f=json
    """
    # Stream ArcGIS REST API endpoint for reservoir data
    # TODO: Replace with actual Stream ArcGIS Feature Server URL
    arcgis_url = "https://services.arcgis.com/your-service/FeatureServer/0"
    
    try:
        # Query the ArcGIS Feature Server
        query_url = f"{arcgis_url}/query?where=1=1&outFields=*&f=json"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(query_url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract reservoir data from features
        reservoir_data = {}
        
        if 'features' in data:
            for feature in data['features']:
                attributes = feature.get('attributes', {})
                
                # Extract reservoir name and capacity percentage
                # Adjust field names based on actual ArcGIS schema
                reservoir_name = attributes.get('name') or attributes.get('reservoir_name') or attributes.get('Reservoir')
                capacity_percentage = attributes.get('capacity_percentage') or attributes.get('percentage') or attributes.get('level')
                
                if reservoir_name and capacity_percentage is not None:
                    # Convert to float if possible
                    try:
                        capacity_percentage = float(capacity_percentage)
                    except (ValueError, TypeError):
                        continue
                    
                    reservoir_data[reservoir_name] = {
                        "percentage": capacity_percentage,
                        "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "latitude": attributes.get('latitude'),
                        "longitude": attributes.get('longitude')
                    }
        
        print(f"Extracted {len(reservoir_data)} reservoir entries from Stream API")
        return reservoir_data
        
    except requests.RequestException as e:
        print(f"Error fetching Stream API data: {e}")
        return {}
    except Exception as e:
        print(f"Error processing Stream API data: {e}")
        return {}

def fetch_reservoir_levels():
    """
    Main function to fetch reservoir levels from Stream API.
    Returns dictionary with format: {reservoir_name: {"percentage": float, "timestamp": str, "latitude": float, "longitude": float}}
    """
    return fetch_stream_reservoir_data()