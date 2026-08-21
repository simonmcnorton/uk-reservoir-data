import csv
import json
import difflib
from datetime import datetime, timezone
from typing import List, Dict, Any

# Adjust import depending on your directory structure (e.g. from scrapers.stream_api import ...)
try:
    from scrapers.stream_api import fetch_reservoir_levels
except ImportError:
    from stream_api import fetch_reservoir_levels


def read_metadata(csv_file: str) -> List[Dict[str, Any]]:
    """
    Read reservoir metadata from CSV file.
    Returns a list of dictionaries with reservoir base information.
    """
    reservoirs = []
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                reservoirs.append({
                    'reservoir_id': row['reservoir_id'],
                    'name': row['name'].strip(),
                    'company': row.get('company', '').strip(),
                    'latitude': float(row['latitude']),
                    'longitude': float(row['longitude']),
                    'total_capacity': row.get('total_capacity', '')
                })
        print(f"Loaded {len(reservoirs)} reservoirs from metadata")
        return reservoirs
    except FileNotFoundError:
        print(f"Error: Metadata file '{csv_file}' not found.")
        return []
    except Exception as e:
        print(f"Error reading metadata from '{csv_file}': {e}")
        return []


def merge_with_live_data(metadata: List[Dict[str, Any]], live_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge metadata with live percentage data using difflib with a 0.8 cutoff threshold.
    Sets 'capacity_percentage' to None (JSON null) if no match meets the threshold.
    """
    merged_data = []
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Available API reservoir names
    api_names = list(live_data.keys())
    
    for reservoir in metadata:
        name = reservoir['name']
        matched_data = None
        matched_name = None
        
        # 1. Exact match check
        if name in live_data:
            matched_name = name
            matched_data = live_data[name]
        else:
            # 2. Fuzzy match with difflib (cutoff 0.8)
            close_matches = difflib.get_close_matches(name, api_names, n=1, cutoff=0.8)
            if close_matches:
                matched_name = close_matches[0]
                matched_data = live_data[matched_name]
                print(f"Fuzzy match: '{name}' -> '{matched_name}'")
        
        if matched_data:
            capacity_percentage = matched_data.get('percentage')
            timestamp = matched_data.get('timestamp', current_time)
            
            record = {
                'reservoir_id': reservoir['reservoir_id'],
                'reservoir_name': reservoir['name'],
                'company': reservoir['company'],
                'capacity_percentage': capacity_percentage,
                'latitude': reservoir['latitude'],
                'longitude': reservoir['longitude'],
                'total_capacity': reservoir.get('total_capacity', ''),
                'last_updated': timestamp,
                'matched_api_name': matched_name
            }
        else:
            # No match found within 0.8 threshold -> output null for capacity_percentage
            record = {
                'reservoir_id': reservoir['reservoir_id'],
                'reservoir_name': reservoir['name'],
                'company': reservoir['company'],
                'capacity_percentage': None,
                'latitude': reservoir['latitude'],
                'longitude': reservoir['longitude'],
                'total_capacity': reservoir.get('total_capacity', ''),
                'last_updated': current_time,
                'matched_api_name': None
            }
            
        merged_data.append(record)
    
    return merged_data


def save_to_json(data: List[Dict[str, Any]], filename: str = "reservoirs.json") -> None:
    """
    Save merged reservoir data to a JSON file (None values serialize to null).
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")


def main():
    """
    Main aggregation pipeline execution.
    """
    print("Starting reservoir data aggregation pipeline...")
    
    # Step 1: Read metadata
    metadata = read_metadata('metadata.csv')
    if not metadata:
        print("No metadata available. Aborting.")
        return
    
    # Step 2: Fetch live data from Stream ArcGIS API
    print("\nFetching live data from Stream ArcGIS API...")
    live_data = fetch_reservoir_levels()
    
    if not live_data:
        print("Warning: No live data returned from Stream API. Proceeding with null capacity levels.")
    
    # Step 3: Merge metadata and live data
    print("\nMerging metadata with live API data...")
    merged_data = merge_with_live_data(metadata, live_data)
    
    matched_count = sum(1 for r in merged_data if r['capacity_percentage'] is not None)
    unmatched_count = len(merged_data) - matched_count
    print(f"\nResults: {matched_count} matched with live data, {unmatched_count} unmatched (null).")
    
    # Step 4: Save to reservoirs.json
    print(f"\nWriting {len(merged_data)} records to reservoirs.json...")
    save_to_json(merged_data, filename="reservoirs.json")
    
    print("\nAggregation complete!")


if __name__ == "__main__":
    main()