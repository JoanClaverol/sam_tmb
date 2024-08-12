import pandas as pd
import uuid

def extract_routes(data):
    """
    Extracts route information from the JSON data and returns a DataFrame with the route details.

    Parameters:
    - data (dict): A dictionary containing the journey plan information.

    Returns:
    - routes_df (pandas.DataFrame): A DataFrame containing the route information
    """
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

        routes_df = pd.json_normalize(routes, 'legs', ['id', 'duration', 'transfers', 'modes'])

    return routes_df