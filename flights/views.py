from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from .amadeus_client import AmadeusClient
from datetime import datetime
import re


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
        origin = request.POST.get('origin', '').strip().upper()
        destination = request.POST.get('destination', '').strip().upper()
        departure_date = request.POST.get('departure_date', '')
        adults_str = request.POST.get('adults', '1')
        
        # Validation
        errors = []
        
        # Check for empty fields
        if not all([origin, destination, departure_date]):
            errors.append('Please fill in all required fields.')
            
        # Validate IATA codes (3 letters)
        iata_pattern = re.compile(r'^[A-Z]{3}$')
        if origin and not iata_pattern.match(origin):
            errors.append(f'Invalid origin code: {origin}. Must be a 3-letter IATA code.')
        if destination and not iata_pattern.match(destination):
            errors.append(f'Invalid destination code: {destination}. Must be a 3-letter IATA code.')
            
        # Check if origin and destination are the same
        if origin and destination and origin == destination:
            errors.append('Origin and destination cannot be the same.')
            
        # Validate date (not in past)
        if departure_date:
            try:
                dept_date_obj = datetime.strptime(departure_date, '%Y-%m-%d').date()
                if dept_date_obj < datetime.now().date():
                    errors.append('Departure date cannot be in the past.')
            except ValueError:
                errors.append('Invalid date format.')
        
        # Validate adults
        try:
            adults = int(adults_str)
            if adults < 1 or adults > 9:
                errors.append('Number of adults must be between 1 and 9.')
        except ValueError:
            errors.append('Invalid number of passengers.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('index')
        
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
                except Exception:
                    # Skip flights with parsing errors
                    continue
            
            # Find the lowest price
            if processed_flights:
                try:
                    min_price = min(float(flight['price']) for flight in processed_flights)
                    for flight in processed_flights:
                        flight['is_cheapest'] = float(flight['price']) == min_price
                except ValueError:
                    # Handle cases where price might not be a valid float
                    pass
            
            return render(request, 'flights/results.html', {
                'flights': processed_flights,
                'origin': origin,
                'destination': destination,
                'departure_date': departure_date,
                'adults': adults,
                'error': None
            })
            
        except Exception as e:
            return render(request, 'flights/results.html', {
                'error': str(e),
                'origin': origin,
                'destination': destination,
                'departure_date': departure_date,
                'adults': locals().get('adults', 1),
                'flights': []
            })
    
    # If GET request, redirect to home
    return render(request, 'flights/index.html')


def airport_search(request):
    """API endpoint for airport autocomplete."""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'locations': []})
    
    try:
        locations = amadeus.search_locations(query)
        results = []
        for loc in locations:
            # We want to show both city and airport name if available
            name = loc.get('name', '')
            iata = loc.get('iataCode', '')
            sub_type = loc.get('subType', '')
            city = loc.get('address', {}).get('cityName', '')
            
            label = f"{name} ({iata})"
            if city and city.lower() != name.lower():
                label = f"{city}, {label}"
                
            results.append({
                'id': iata,
                'label': label,
                'subType': sub_type,
                'city': city,
                'airport_name': name
            })
            
        return JsonResponse({'locations': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
