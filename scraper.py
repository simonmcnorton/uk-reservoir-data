import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_thames_water_reservoirs():
    """
    Scrape reservoir data from Thames Water website
    """
    url = "https://www.thameswater.co.uk/about-us/performance/reservoir-levels-and-rainfall-figures"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the reservoir section
        reservoir_data = []
        
        # Look for the water levels section
        water_levels_section = soup.find(string=re.compile("Water levels in our reservoirs"))
        if water_levels_section:
            # Get the parent element to find the list
            parent = water_levels_section.find_parent()
            if parent:
                # Find the list items after the section
                list_items = parent.find_next('ul')
                if list_items:
                    for li in list_items.find_all('li'):
                        text = li.get_text()
                        # Extract reservoir name and percentage
                        # Pattern: "Reservoirs in London were 74% full"
                        match = re.search(r'(.+?)\s+were\s+(\d+)%\s+full', text)
                        if match:
                            name = match.group(1).strip()
                            percentage = float(match.group(2))
                            reservoir_data.append({
                                "reservoir_name": name,
                                "capacity_percentage": percentage,
                                "company": "Thames Water"
                            })
                        # Pattern: "Farmoor Reservoir in Oxfordshire was 92% full"
                        match2 = re.search(r'(.+?)\s+was\s+(\d+)%\s+full', text)
                        if match2:
                            name = match2.group(1).strip()
                            percentage = float(match2.group(2))
                            reservoir_data.append({
                                "reservoir_name": name,
                                "capacity_percentage": percentage,
                                "company": "Thames Water"
                            })
        
        # Also try to find specific breakdowns like "(72% full in West London and 82% full in Lee Valley)"
        # Pattern: "(\d+)%\s+full\s+in\s+(.+?)(?:\s+and|$)"
        if parent:
            list_items = parent.find_next('ul')
            if list_items:
                for li in list_items.find_all('li'):
                    text = li.get_text()
                    # Look for patterns like "72% full in West London"
                    for match in re.finditer(r'(\d+)%\s+full\s+in\s+(.+?)(?:\s+and|\)|,|$)', text):
                        percentage = float(match.group(1))
                        name = match.group(2).strip()
                        # Only add if not already in the list
                        if not any(r["reservoir_name"] == name for r in reservoir_data):
                            reservoir_data.append({
                                "reservoir_name": name,
                                "capacity_percentage": percentage,
                                "company": "Thames Water"
                            })
        
        print(f"Extracted {len(reservoir_data)} reservoir entries:")
        for reservoir in reservoir_data:
            print(f"  - {reservoir['reservoir_name']}: {reservoir['capacity_percentage']}%")
        
        return reservoir_data
        
    except requests.RequestException as e:
        print(f"Error fetching the page: {e}")
        return []
    except Exception as e:
        print(f"Error parsing the page: {e}")
        return []

def save_to_json(data, filename="reservoirs.json"):
    """
    Save reservoir data to JSON file
    """
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")

if __name__ == "__main__":
    # Scrape the data
    reservoir_data = scrape_thames_water_reservoirs()
    
    # Save to JSON
    if reservoir_data:
        save_to_json(reservoir_data)
    else:
        print("No reservoir data extracted")