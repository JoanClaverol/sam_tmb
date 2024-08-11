import json
import pandas as pd

# Specify the file path
file_path = './data/journey_plan_2024-08-07_11-43.json'

# Read the JSON file
with open(file_path, 'r') as file:
    journey_plan = json.load(file)


import uuid

def extract_routes(data):
    routes = []

    if 'plan' in data and 'itineraries' in data['plan']:
        for itinerary in data['plan']['itineraries']:
            route = {
                'id': str(uuid.uuid4()),  # Unique identifier
                'duration': itinerary.get('duration'),
                'transfers': itinerary.get('transfers'),
                'legs': [],
                'modes': set()  # Use a set to collect unique modes
            }
            
            for leg in itinerary.get('legs', []):
                leg_info = {
                    'mode': leg.get('mode'),
                    'start_time': leg.get('startTime'),
                    'end_time': leg.get('endTime'),
                    'from': leg.get('from', {}).get('name'),
                    'to': leg.get('to', {}).get('name'),
                    'route': leg.get('route'),
                    'distance': leg.get('distance'),
                    'agency': leg.get('agencyName')
                }
                route['legs'].append(leg_info)
                route['modes'].add(leg.get('mode'))  # Add the mode to the set
            
            route['modes'] = list(route['modes'])  # Convert the set to a list
            routes.append(route)
    
    return routes

# Extract route information
routes = extract_routes(journey_plan)


routes_df = pd.json_normalize(routes, 'legs', ['id', 'duration', 'transfers', 'modes'])



if __name__ == '__main__':
    print(routes_df.sort_values(['id', 'start_time']))