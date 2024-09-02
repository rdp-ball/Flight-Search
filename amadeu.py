from amadeus import Client, ResponseError

# Initialize the Amadeus client
amadeus = Client(
    client_id='8zAQaOrWiKQnWpS1W5dAoGKyApdr2zmH',
    client_secret='4dZJVCV22xIwROU7'
)

def search_flights(origin, destination, departure_date, adults=1):
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=adults
        )
        return response.data
    except ResponseError as error:
        return str(error)

def main():
    # Define search parameters
    origin = 'MAD'
    destination = 'ATH'
    departure_date = '2024-11-01'
    adults = 1

    # Call the search_flights function
    result = search_flights(origin, destination, departure_date, adults)

    # Print the result
    print("Flight search results:\n", result)

if __name__ == "__main__":
    main()
