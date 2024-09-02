import streamlit as st
from amadeus import Client, ResponseError
from openai import OpenAI
import json
import re

# Initialize the Amadeus client
load_dotenv()

# Initialize the Amadeus client
amadeus = Client(
    client_id=os.getenv('AMADEUS_CLIENT_ID'),
    client_secret=os.getenv('AMADEUS_CLIENT_SECRET')
)
# Initialize OpenAI client
client = OpenAI(base_url="http://localhost:8000/v1", api_key="lm-studio")

def extract_dict_from_message(message):
    try:
        # Print the raw message for debugging
        print("Raw message for extraction:", message)
        
        # Remove comments and clean up the JSON string
        cleaned_message = re.sub(r'//.*$', '', message, flags=re.MULTILINE)
        
        # Find the dictionary within the cleaned message
        # Simplified regex to match JSON objects
        match = re.search(r'\{(?:[^{}"]|"(?:\\.|[^"\\])*")*\}', cleaned_message, re.DOTALL)
        if match:
            dict_str = match.group(0)
            
            # Replace single quotes with double quotes
            dict_str = re.sub(r"(?<!\\)'", '"', dict_str)
            
            # Print the cleaned dictionary string for debugging
            print("Cleaned dictionary string:", dict_str)
            
            # Safely parse the JSON string
            extracted_dict = json.loads(dict_str)
            print("Extracted dictionary:", extracted_dict)  # Debug: check extracted dictionary
            return extracted_dict
        else:
            print("No dictionary found in the message.")
            return None
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error extracting dictionary: {e}")
        return None


def convert_prompt_to_parameters(prompt):
    response = client.chat.completions.create(
        model="QuantFactory/Meta-Llama-3-8B-Instruct-GGUF",
        messages=[
            {"role": "system", "content": '''Convert the following natural language prompt into parameters for an Amadeus API flight search.
            Example format:
            {
                "origin": "BOM",
                "destination": "HYD",
                "departure_date": "2024-08-04",
                "adults": 1,
                "airline": "AIR INDIA",
                "terminal": 2,
                "duration": "1hr 25min",
                "bookable_seats": 10
            }
            '''},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    
    content = response.choices[0].message.content
    st.write("Raw LLM response:", content)  # Debug: check raw response
    
    parameters = extract_dict_from_message(content)
    
    if parameters:
        cleaned_parameters = {
            "origin": parameters.get('origin', '').upper(),
            "destination": parameters.get('destination', '').upper(),
            "departure_date": parameters.get('departure_date', '').strip(),
            "adults": parameters.get('adults', 1),
            "airline": parameters.get('airline', ''),
            "terminal": parameters.get('terminal', ''),
            "duration": parameters.get('duration', ''),
            "bookable_seats": parameters.get('bookable_seats', 0)
        }
        
        for key in ['origin', 'destination', 'departure_date', 'adults']:
            if not cleaned_parameters[key]:
                st.error(f"Missing required parameter: {key}")
                return {}
        
        return cleaned_parameters
    else:
        st.error("Failed to extract parameters from the response.")
        return {}

def search_flights(origin, destination, departure_date, adults=1, airline='', terminal='', duration='', bookable_seats=0):
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=adults
        )
        flights = response.data
        filtered_flights = []

        for flight in flights:
            # Apply filtering based on additional parameters
            if airline and airline not in flight.get('validatingAirlineCodes', []):
                continue
            if duration:
                flight_duration = flight.get('itineraries', [{}])[0].get('duration', '')
                if duration not in flight_duration:
                    continue
            if bookable_seats and flight.get('numberOfBookableSeats', 0) < bookable_seats:
                continue
            filtered_flights.append(flight)

        return filtered_flights
    except ResponseError as error:
        return str(error)

def main():
    st.title('Flight Search App')

    prompt = st.text_area('Enter your flight search query')

    if st.button('Search Flights'):
        if prompt:
            parameters = convert_prompt_to_parameters(prompt)
            
            if parameters:
                origin = parameters.get('origin', 'N/A')
                destination = parameters.get('destination', 'N/A')
                departure_date = parameters.get('departure_date', 'N/A')
                airline = parameters.get('airline', '')
                terminal = parameters.get('terminal', '')
                duration = parameters.get('duration', '')
                bookable_seats_str = parameters.get('bookable_seats', '0')
                adults_str = parameters.get('adults', '1')
                
                try:
                    adults = int(adults_str) if adults_str else 1
                except ValueError:
                    adults = 1
                
                try:
                    bookable_seats = int(bookable_seats_str) if bookable_seats_str else 0
                except ValueError:
                    bookable_seats = 0
                
                result = search_flights(
                    origin, destination, departure_date, adults, airline, terminal, duration, bookable_seats
                )
                
                if isinstance(result, str):
                    st.error(result)
                else:
                    st.write("### Flight Results:")
                    if isinstance(result, list):
                        for offer in result:
                            flight_id = offer.get('id', 'N/A')
                            price = offer.get('price', {}).get('total', 'N/A')
                            departure_date = offer.get('itineraries', [{}])[0].get('segments', [{}])[0].get('departure', {}).get('at', 'N/A')
                            airline = offer.get('validatingAirlineCodes', ['N/A'])[0]  # Example extraction
                            terminal = offer.get('terminal', 'N/A')
                            duration = offer.get('itineraries', [{}])[0].get('duration', 'N/A')
                            bookable_seats = offer.get('numberOfBookableSeats', 'N/A')

                            st.write(f"**Flight ID:** {flight_id}")
                            st.write(f"**Price:** {price}")
                            st.write(f"**Departure Date:** {departure_date}")
                            st.write(f"**Airline:** {airline}")
                            st.write(f"**Terminal:** {terminal}")
                            st.write(f"**Duration:** {duration}")
                            st.write(f"**Bookable Seats:** {bookable_seats}")
                            st.write("---")
                    else:
                        st.write("No flights found.")
        else:
            st.write("Please enter a prompt.")

if __name__ == "__main__":
    main()
