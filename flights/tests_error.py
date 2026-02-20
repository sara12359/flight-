from django.test import SimpleTestCase, Client
from django.urls import reverse
from unittest.mock import patch
from datetime import datetime, timedelta

class FlightErrorHandlingTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()
        self.search_url = reverse('search')
        self.index_url = reverse('index')

    def test_missing_fields(self):
        response = self.client.post(self.search_url, {
            'origin': '',
            'destination': 'LHR',
            'departure_date': '',
            'adults': 1
        }, follow=True)
        self.assertRedirects(response, self.index_url)
        messages = list(response.context['messages'])
        self.assertTrue(any('Please fill in all required fields' in str(m) for m in messages))

    def test_invalid_airport_codes(self):
        response = self.client.post(self.search_url, {
            'origin': 'INVALID',
            'destination': '123',
            'departure_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'adults': 1
        }, follow=True)
        messages = [str(m) for m in response.context['messages']]
        self.assertTrue(any('Invalid origin code' in m for m in messages))
        self.assertTrue(any('Invalid destination code' in m for m in messages))

    def test_same_origin_destination(self):
        response = self.client.post(self.search_url, {
            'origin': 'JFK',
            'destination': 'JFK',
            'departure_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'adults': 1
        }, follow=True)
        messages = [str(m) for m in response.context['messages']]
        self.assertIn('Origin and destination cannot be the same.', messages)

    def test_past_date(self):
        past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.post(self.search_url, {
            'origin': 'JFK',
            'destination': 'LHR',
            'departure_date': past_date,
            'adults': 1
        }, follow=True)
        messages = [str(m) for m in response.context['messages']]
        self.assertIn('Departure date cannot be in the past.', messages)

    @patch('flights.views.amadeus.search_flights')
    def test_api_failure_graceful_handling(self, mock_search):
        mock_search.side_effect = Exception("API Error: Destination airport not found")
        
        response = self.client.post(self.search_url, {
            'origin': 'JFK',
            'destination': 'ZZZ',
            'departure_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'adults': 1
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "API Error: Destination airport not found")
        self.assertIn('origin', response.context)
        self.assertEqual(response.context['origin'], 'JFK')

    @patch('flights.views.amadeus.search_flights')
    def test_empty_results_handling(self, mock_search):
        mock_search.return_value = []
        
        response = self.client.post(self.search_url, {
            'origin': 'JFK',
            'destination': 'LHR',
            'departure_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'adults': 1
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No Flights Found")
