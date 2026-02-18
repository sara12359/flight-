import os
import django
from unittest.mock import patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flight_project.settings')
django.setup()

from django.test import Client

def run_manual_test():
    print("Starting manual test...")
    client = Client()
    
    mock_flights = [
        {'price': {'total': '200.00', 'currency': 'USD'}, 'itineraries': [{'segments': [{'carrierCode': 'AA', 'number': '100', 'departure': {'iataCode': 'JFK', 'at': '2023-10-10T10:00:00'}, 'arrival': {'iataCode': 'LHR', 'at': '2023-10-10T20:00:00'}}], 'duration': 'P0DT10H0M'}]},
        {'price': {'total': '150.00', 'currency': 'USD'}, 'itineraries': [{'segments': [{'carrierCode': 'BA', 'number': '200', 'departure': {'iataCode': 'JFK', 'at': '2023-10-10T12:00:00'}, 'arrival': {'iataCode': 'LHR', 'at': '2023-10-10T22:00:00'}}], 'duration': 'P0DT10H0M'}]},
        {'price': {'total': '300.00', 'currency': 'USD'}, 'itineraries': [{'segments': [{'carrierCode': 'DL', 'number': '300', 'departure': {'iataCode': 'JFK', 'at': '2023-10-10T14:00:00'}, 'arrival': {'iataCode': 'LHR', 'at': '2023-10-11T00:00:00'}}], 'duration': 'P0DT10H0M'}]},
    ]

    with open('verification_result.txt', 'w', encoding='utf-8') as log_file:
        def log(msg):
            print(msg)
            log_file.write(str(msg) + '\n')

        with patch('flights.views.amadeus.search_flights') as mock_search:
            mock_search.return_value = mock_flights
            
            try:
                response = client.post('/search/', {
                    'origin': 'JFK',
                    'destination': 'LHR',
                    'departure_date': '2023-10-10',
                    'adults': 1
                })
                
                log(f"Response status: {response.status_code}")
                if response.status_code != 200:
                    log("Response content (snippet):")
                    log(response.content.decode('utf-8')[:5000]) # First 500 characters
                    return

                flights = response.context['flights']
                log(f"Number of flights in context: {len(flights)}")
                
                for i, f in enumerate(flights):
                    log(f"Flight {i}: Price={f.get('price')}, Cheapest={f.get('is_cheapest')}")
                    
                prices = [f['price'] for f in flights]
                flags = [f.get('is_cheapest', False) for f in flights]
                
                expected_prices = ['200.00', '150.00', '300.00']
                expected_flags = [False, True, False]
                
                if prices == expected_prices and flags == expected_flags:
                    log("TEST PASSED")
                else:
                    log("TEST FAILED")
                    log(f"Expected prices: {expected_prices}, Got: {prices}")
                    log(f"Expected flags: {expected_flags}, Got: {flags}")
                    
            except Exception as e:
                log(f"Exception occurred: {e}")
                import traceback
                traceback.print_exc(file=log_file)

if __name__ == '__main__':
    run_manual_test()
