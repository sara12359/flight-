from django.shortcuts import render
from django.http import JsonResponse
from .amadeus_client import AmadeusClient
from datetime import datetime


# Initialize Amadeus client with your credentials
API_KEY = "zI1g5568Q4zKYcD1TJzKy79AxAG6Yqup"
API_SECRET = "NFav8fay8A1EVfnb"
amadeus = AmadeusClient(API_KEY, API_SECRET)


def index(request):
    """Render the flight search home page."""
    return render(request, 'flights/index.html')


def search(request):
    """Handle flight search requests."""
    if request.method == 'POST':
        origin = request.POST.get('origin', '')
        destination = request.POST.get('destination', '')
        departure_date = request.POST.get('departure_date', '')
        adults = int(request.POST.get('adults', 1))
        
        # Validate inputs
        if not all([origin, destination, departure_date]):
            return render(request, 'flights/results.html', {
                'error': 'Please fill in all required fields.',
                'flights': []
            })
        
        try:
            # Search for flights
            flights = amadeus.search_flights(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                adults=adults,
                max_results=20
            )
            
            # Process flight data for template
            processed_flights = []
            for flight in flights:
                try:
                    # Extract relevant information
                    itineraries = flight.get('itineraries', [])
                    price = flight.get('price', {})
                    
                    if itineraries:
                        first_itinerary = itineraries[0]
                        segments = first_itinerary.get('segments', [])
                        
                        if segments:
                            first_segment = segments[0]
                            last_segment = segments[-1]
                            
                            flight_data = {
                                'airline': first_segment.get('carrierCode', 'N/A'),
                                'flight_number': first_segment.get('number', 'N/A'),
                                'departure_airport': first_segment.get('departure', {}).get('iataCode', 'N/A'),
                                'arrival_airport': last_segment.get('arrival', {}).get('iataCode', 'N/A'),
                                'departure_time': first_segment.get('departure', {}).get('at', 'N/A'),
                                'arrival_time': last_segment.get('arrival', {}).get('at', 'N/A'),
                                'duration': first_itinerary.get('duration', 'N/A'),
                                'stops': len(segments) - 1,
                                'price': price.get('total', 'N/A'),
                                'currency': price.get('currency', 'USD'),
                            }
                            processed_flights.append(flight_data)
                except Exception as e:
                    # Skip flights with parsing errors
                    continue
            
            return render(request, 'flights/results.html', {
                'flights': processed_flights,
                'origin': origin.upper(),
                'destination': destination.upper(),
                'departure_date': departure_date,
                'error': None
            })
            
        except Exception as e:
            return render(request, 'flights/results.html', {
                'error': f'Error searching flights: {str(e)}',
                'flights': []
            })
    
    # If GET request, redirect to home
    return render(request, 'flights/index.html')
