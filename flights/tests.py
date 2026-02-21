from django.test import SimpleTestCase, Client
from unittest.mock import patch

class FlightSearchTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    @patch('flights.views.amadeus.search_flights')
    def test_cheapest_flight_highlight(self, mock_search):
        # Mock flight data
        mock_flights = [
            {
                'price': {'total': '200.00', 'currency': 'USD'},
                'itineraries': [{
                    'segments': [{
                        'carrierCode': 'AA',
                        'number': '100',
                        'departure': {'iataCode': 'JFK', 'at': '2023-10-10T10:00:00'},
                        'arrival': {'iataCode': 'LHR', 'at': '2023-10-10T20:00:00'}
                    }],
                    'duration': 'P0DT10H0M'
                }]
            },
            {
                'price': {'total': '150.00', 'currency': 'USD'},
                'itineraries': [{
                    'segments': [{
                        'carrierCode': 'BA',
                        'number': '200',
                        'departure': {'iataCode': 'JFK', 'at': '2023-10-10T12:00:00'},
                        'arrival': {'iataCode': 'LHR', 'at': '2023-10-10T22:00:00'}
                    }],
                    'duration': 'P0DT10H0M'
                }]
            },
            {
                'price': {'total': '300.00', 'currency': 'USD'},
                'itineraries': [{
                    'segments': [{
                        'carrierCode': 'DL',
                        'number': '300',
                        'departure': {'iataCode': 'JFK', 'at': '2023-10-10T14:00:00'},
                        'arrival': {'iataCode': 'LHR', 'at': '2023-10-11T00:00:00'}
                    }],
                    'duration': 'P0DT10H0M'
                }]
            },
        ]
        mock_search.return_value = mock_flights

        response = self.client.post('/search/', {
            'origin': 'JFK',
            'destination': 'LHR',
            'departure_date': '2026-12-25',
            'adults': 1
        })

        self.assertEqual(response.status_code, 200)
        flights = response.context['flights']
        self.assertEqual(len(flights), 3)
        
        # Check prices and flags
        # processed_flights stores 'price' as string/value directly from extraction
        # Views logic:
        # price = price.get('total', 'N/A') -> '200.00'
        # Then views converts to float for comparison
        
        prices = [f['price'] for f in flights]
        self.assertEqual(prices, ['200.00', '150.00', '300.00'])
        
        flags = [f.get('is_cheapest', False) for f in flights]
        self.assertEqual(flags, [False, True, False])
