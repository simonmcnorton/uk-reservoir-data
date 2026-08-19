import csv
import json
from datetime import datetime, timezone
from scrapers.thames import scrape_thames_water_reservoirs

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
                    'longitude': float(row['longitude'])
                })
        print(f"Loaded {len(reservoirs)} reservoirs from metadata")
        return reservoirs
    except Exception as e:
        print(f"Error reading metadata: {e}")
        return []

def merge_with_live_data(metadata, live_percentages):
    """
    Merge metadata with live percentage data
    Returns a list of complete reservoir records
    """
    merged_data = []
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    for reservoir in metadata:
        name = reservoir['name']
        # Try to find matching live data by name
        capacity_percentage = live_percentages.get(name)
        
        if capacity_percentage is not None:
            merged_record = {
                'reservoir_id': reservoir['reservoir_id'],
                'name': reservoir['name'],
                'company': reservoir['company'],
                'capacity_percentage': capacity_percentage,
                'latitude': reservoir['latitude'],
                'longitude': reservoir['longitude'],
                'last_updated': current_time
            }
            merged_data.append(merged_record)
        else:
            print(f"Warning: No live data found for {name}")
            # Still include the reservoir but with None for percentage
            merged_record = {
                'reservoir_id': reservoir['reservoir_id'],
                'name': reservoir['name'],
                'company': reservoir['company'],
                'capacity_percentage': None,
                'latitude': reservoir['latitude'],
                'longitude': reservoir['longitude'],
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
    
    # Step 2: Scrape live data
    print("\nScraping live data...")
    live_percentages = scrape_thames_water_reservoirs()
    
    if not live_percentages:
        print("No live data scraped. Exiting.")
        return
    
    # Step 3: Merge data
    print("\nMerging data...")
    merged_data = merge_with_live_data(metadata, live_percentages)
    
    # Step 4: Save to JSON
    print(f"\nSaving {len(merged_data)} reservoir records...")
    save_to_json(merged_data)
    
    print("\nAggregation complete!")

if __name__ == "__main__":
    main()