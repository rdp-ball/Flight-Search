import streamlit as st
from openai import OpenAI
from amadeus import Client, ResponseError

# Initialize Amadeus client
load_dotenv()

# Initialize the Amadeus client
amadeus = Client(
    client_id=os.getenv('AMADEUS_CLIENT_ID'),
    client_secret=os.getenv('AMADEUS_CLIENT_SECRET')
)
# Function to interact with LM Studio
def interact_with_llm(text):
    client = OpenAI(base_url="http://localhost:8000/v1", api_key="lm-studio")

    completion = client.chat.completions.create(
        model="QuantFactory/Meta-Llama-3-8B-Instruct-GGUF",
        messages=[
            {"role": "system", "content": """return a python dictionary that contains only the following info: to location, from location, date all of them as python strings and no explanation required.
                                             For example the dictionary should look like {"from_location": "MAD", "to_location": "BAN", "date": "2024-11-01"} if the user is going to Madras, from Bangalore on 2024-11-01."""},
            {"role": "user", "content": text}
        ],
        temperature=0.7,
    )

    response = completion.choices[0].message['content']
    return eval(response)  # Convert string representation of dictionary to actual dictionary

# Function to search for flights using Amadeus API
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

# Streamlit app
st.title("Flight Search App")

with st.form("flight_search_form"):
    user_input = st.text_area("Enter your travel request:")
    submitted = st.form_submit_button("Submit")

    if submitted:
        llm_response = interact_with_llm(user_input)
        origin = llm_response['from_location']
        destination = llm_response['to_location']
        departure_date = llm_response['date']
        
        flight_results = search_flights(origin, destination, departure_date)
        
        st.write("Flight Search Results:")
        st.write(flight_results)
