import streamlit as st
from amadeus import Client, ResponseError
import datetime
from openai import OpenAI

# Initialize the Amadeus client
amadeus = Client(
    client_id='8zAQaOrWiKQnWpS1W5dAoGKyApdr2zmH',
    client_secret='4dZJVCV22xIwROU7'
)

# Initialize OpenAI client
client = OpenAI(base_url="http://localhost:8000/v1", api_key="lm-studio")

def convert_prompt_to_parameters(prompt):
    response = client.chat.completions.create(
        model="QuantFactory/Meta-Llama-3-8B-Instruct-GGUF",
        messages=[
            {"role": "system", "content": "Convert the following natural language prompt into parameters for an Amadeus API flight search."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    # Extract the content correctly
    response_message = response.choices[0].message.content
    return response_message
   # content = response.choices[0].message['content']
    #return content

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

    # Input field for natural language prompt
    prompt = st.text_area('Enter your flight search query')

    if st.button('Search Flights'):
        if prompt:
            # Convert prompt to parameters
            parameters = convert_prompt_to_parameters(prompt)
            
            # Assuming parameters is a string in the format "origin, destination, departure_date, adults"
            params = parameters.split(',')
            if len(params) >= 3:
                origin, destination, departure_date = params[0].strip(), params[1].strip(), params[2].strip()
                adults = int(params[3].strip()) if len(params) > 3 else 1
                
                # Call the search_flights function
                result = search_flights(origin, destination, departure_date, adults)
                
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
        else:
            st.write("Please enter a prompt.")

if __name__ == "__main__":
    main()
