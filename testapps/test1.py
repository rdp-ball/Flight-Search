import streamlit as st
from amadeus import Client, ResponseError
import datetime

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
    st.title('Flight Search App')

    # Input fields
    origin = st.text_input('Origin Airport Code', 'MAD')
    destination = st.text_input('Destination Airport Code', 'ATH')
    
    # Use datetime.date object for date_input
    departure_date = st.date_input('Departure Date', value=datetime.date(2024, 11, 1))
    adults = st.number_input('Number of Adults', min_value=1, value=1)

    if st.button('Search Flights'):
        # Call the search_flights function
        result = search_flights(origin, destination, departure_date.strftime('%Y-%m-%d'), adults)
        
        if isinstance(result, str):  # In case of an error
            st.error(result)
        else:
            # Display relevant data
            st.write("### Flight Results:")
            if isinstance(result, list):
                for offer in result:
                    flight_id = offer.get('id', 'N/A')
                    price = offer.get('price', {}).get('total', 'N/A')
                    departure_date = offer.get('itineraries', [{}])[0].get('segments', [{}])[0].get('departure', {}).get('at', 'N/A')

                    st.write(f"**Flight ID:** {flight_id}")
                    st.write(f"**Price:** {price}")
                    st.write(f"**Departure Date:** {departure_date}")
                    st.write("---")
            else:
                st.write("No flights found.")

if __name__ == "__main__":
    main()
