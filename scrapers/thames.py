import requests
from bs4 import BeautifulSoup
import re

def scrape_thames_water_reservoirs():
    """
    Scrape reservoir data from Thames Water website
    Returns a dictionary mapping reservoir names to their capacity percentages
    """
    url = "https://www.thameswater.co.uk/about-us/performance/reservoir-levels-and-rainfall-figures"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Dictionary to store reservoir name -> percentage mapping
        reservoir_percentages = {}
        
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
                            reservoir_percentages[name] = percentage
                        # Pattern: "Farmoor Reservoir in Oxfordshire was 92% full"
                        match2 = re.search(r'(.+?)\s+was\s+(\d+)%\s+full', text)
                        if match2:
                            name = match2.group(1).strip()
                            percentage = float(match2.group(2))
                            reservoir_percentages[name] = percentage
        
        # Also try to find specific breakdowns like "(72% full in West London and 82% full in Lee Valley)"
        if parent:
            list_items = parent.find_next('ul')
            if list_items:
                for li in list_items.find_all('li'):
                    text = li.get_text()
                    # Look for patterns like "72% full in West London"
                    for match in re.finditer(r'(\d+)%\s+full\s+in\s+(.+?)(?:\s+and|\)|,|$)', text):
                        percentage = float(match.group(1))
                        name = match.group(2).strip()
                        # Only add if not already in the dictionary
                        if name not in reservoir_percentages:
                            reservoir_percentages[name] = percentage
        
        print(f"Extracted {len(reservoir_percentages)} reservoir entries:")
        for name, percentage in reservoir_percentages.items():
            print(f"  - {name}: {percentage}%")
        
        return reservoir_percentages
        
    except requests.RequestException as e:
        print(f"Error fetching the page: {e}")
        return {}
    except Exception as e:
        print(f"Error parsing the page: {e}")
        return {}