import csv
import json
import difflib
from datetime import datetime, timezone
from scrapers.stream_api import fetch_reservoir_levels

def read_metadata(csv_file):
    """
    Read reservoir metadata from CSV file
    Returns a list of dictionaries with reservoir information
    """
    reservoirs = []
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                reservoirs.append({
                    'reservoir_id': row['reservoir_id'],
                    'name': row['name'],
                    'company': row['company'],
                    'latitude': float(row['latitude']),
                    'longitude': float(row['longitude']),
                    'total_capacity': row.get('total_capacity', '')
                })
        print(f"Loaded {len(reservoirs)} reservoirs from metadata")
        return reservoirs
    except Exception as e:
        print(f"Error reading metadata: {e}")
        return []

def merge_with_live_data(metadata, live_data):
    """
    Merge metadata with live percentage data using difflib for fuzzy matching
    Returns a list of complete reservoir records
    """
    merged_data = []
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Get all available API reservoir names
    api_names = list(live_data.keys())
    
    for reservoir in metadata:
        name = reservoir['name']
        
        # Try exact match first
        if name in live_data:
            matched_data = live_data[name]
        else:
            # Use difflib for fuzzy matching with 0.8 threshold
            close_matches = difflib.get_close_matches(name, api_names, n=1, cutoff=0.8)
            if close_matches:
                matched_name = close_matches[0]
                matched_data = live_data[matched_name]
                print(f"Matched {name} to {matched_name} using fuzzy matching")
            else:
                matched_data = None
        
        if matched_data:
            capacity_percentage = matched_data.get('percentage')
            timestamp = matched_data.get('timestamp', current_time)
            
            merged_record = {
                'reservoir_id': reservoir['reservoir_id'],
                'name': reservoir['name'],
                'company': reservoir['company'],
                'capacity_percentage': capacity_percentage,
                'latitude': reservoir['latitude'],
                'longitude': reservoir['longitude'],
                'total_capacity': reservoir.get('total_capacity', ''),
                'last_updated': timestamp
            }
            merged_data.append(merged_record)
        else:
            # Still include the reservoir but with None for percentage
            merged_record = {
                'reservoir_id': reservoir['reservoir_id'],
                'name': reservoir['name'],
                'company': reservoir['company'],
                'capacity_percentage': None,
                'latitude': reservoir['latitude'],
                'longitude': reservoir['longitude'],
                'total_capacity': reservoir.get('total_capacity', ''),
                'last_updated': current_time
            }
            merged_data.append(merged_record)
    
    return merged_data

def save_to_json(data, filename="reservoirs.json"):
    """
    Save reservoir data to JSON file
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")

def main():
    """
    Main aggregation pipeline
    """
    print("Starting reservoir data aggregation...")
    
    # Step 1: Read metadata
    metadata = read_metadata('metadata.csv')
    if not metadata:
        print("No metadata found. Exiting.")
        return
    
    # Step 2: Fetch live data from Stream API
    print("\nFetching live data from Stream API...")
    live_data = fetch_reservoir_levels()
    
    if not live_data:
        print("No live data available from Stream API - proceeding with metadata only")
    
    # Step 3: Merge data
    print("\nMerging data with live API data...")
    merged_data = merge_with_live_data(metadata, live_data)
    
    # Count how many have live data
    with_live_data = sum(1 for r in merged_data if r['capacity_percentage'] is not None)
    print(f"Matched {with_live_data} reservoirs with live data, {len(merged_data) - with_live_data} without live data")
    
    # Step 4: Save to JSON
    print(f"\nSaving {len(merged_data)} reservoir records...")
    save_to_json(merged_data)
    
    print("\nAggregation complete!")

if __name__ == "__main__":
    main()