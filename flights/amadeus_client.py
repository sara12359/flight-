import requests
from datetime import datetime, timedelta


class AmadeusClient:
    """Client for interacting with Amadeus API."""
    
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        self.base_url = "https://test.api.amadeus.com"
        self.access_token = None
        self.token_expiry = None
    
    def get_token(self):
        """Fetch OAuth2 token from Amadeus API."""
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.api_secret
        }
        
        try:
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data['access_token']
            # Token typically expires in 1799 seconds (30 minutes)
            expires_in = token_data.get('expires_in', 1799)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
            
            return self.access_token
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get access token: {str(e)}")
    
    def search_flights(self, origin, destination, departure_date, adults=1, max_results=10):
        """
        Search for flight offers.
        
        Args:
            origin: IATA code of origin airport (e.g., 'JFK')
            destination: IATA code of destination airport (e.g., 'LAX')
            departure_date: Departure date in YYYY-MM-DD format
            adults: Number of adult travelers (default: 1)
            max_results: Maximum number of results (default: 10)
        
        Returns:
            List of flight offers
        """
        token = self.get_token()
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        params = {
            'originLocationCode': origin.upper(),
            'destinationLocationCode': destination.upper(),
            'departureDate': departure_date,
            'adults': adults,
            'max': max_results
        }
        
        url = f"{self.base_url}/v2/shopping/flight-offers"
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get('data', [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Flight search failed: {str(e)}")
