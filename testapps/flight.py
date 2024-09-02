import streamlit as st
from amadeus import Client, ResponseError
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from huggingface_hub import login
from langchain.llms.huggingface_pipeline import HuggingFacePipeline
from langchain import PromptTemplate, LLMChain
import json
import re
import torch
load_dotenv()
# Log in to Hugging Face
access_token = os.getenv('huggin_face_token')
login(token=access_token)

# Load the text generation model and tokenizer
model_id = "gpt2"  # Replace with an appropriate model if necessary
tokenizer = AutoTokenizer.from_pretrained(model_id, use_auth_token=access_token)
model = AutoModelForCausalLM.from_pretrained(model_id, use_auth_token=access_token)

# Create a text generation pipeline
device = 0 if torch.cuda.is_available() else -1  # Use GPU if available
pipeline_inst = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=50,  # Set max_new_tokens instead of max_length
    num_return_sequences=1,
    device=device  # Set the device
)

# Integrate with LangChain
llm = HuggingFacePipeline(pipeline=pipeline_inst)

# Initialize the Amadeus client


# Initialize the Amadeus client
amadeus = Client(
    client_id=os.getenv('AMADEUS_CLIENT_ID'),
    client_secret=os.getenv('AMADEUS_CLIENT_SECRET')
)

def extract_dict_from_message(message):
    try:
        print("Raw message for extraction:", message)
        
        # Remove comments and clean up the JSON string
        cleaned_message = re.sub(r'//.*$', '', message, flags=re.MULTILINE)
        
        # Find the dictionary within the cleaned message
        # Simplified regex to match JSON objects
        match = re.search(r'\{(?:[^{}"]|"(?:\\.|[^"\\])*")*\}', cleaned_message, re.DOTALL)
        if match:
            dict_str = match.group(0)
            
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
    system_message = '''Convert the following natural language prompt into parameters for an Amadeus API flight search.
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
    '''
    input_text = f"{system_message}\nPrompt: {prompt}"
    response = llm(input_text)
    
    # Debugging: Print the response to understand its structure
    st.write("LLM response type:", type(response))
    st.write("LLM response content:", response)

    if isinstance(response, str):
        content = response
    elif isinstance(response, list) and len(response) > 0 and 'generated_text' in response[0]:
        content = response[0]['generated_text']
    else:
        st.error("Unexpected response format.")
        return {}

    parameters = extract_dict_from_message(content)
    
    if parameters:
        cleaned_parameters = {
            "origin": parameters.get('origin', '').upper(),
            "destination": parameters.get('destination', '').upper(),
            "departure_date": parameters.get('departure_date', '').strip(),
            "adults": parameters.get('adults', 1)
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

def format_flight_data(flight_data):
    input_text = f"Format the following flight data into a human-readable response.\n{json.dumps(flight_data)}"
    response = llm(input_text)
    
    # Debugging: Print the response to understand its structure
    st.write("LLM response type:", type(response))
    st.write("LLM response content:", response)
    
    if isinstance(response, str):
        content = response
    elif isinstance(response, list) and len(response) > 0 and 'generated_text' in response[0]:
        content = response[0]['generated_text']
    else:
        st.error("Unexpected response format.")
        return "Error in formatting flight data."

    return content

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
                            formatted_output = format_flight_data(offer)
                            st.write(formatted_output)
                            st.write("---")
                    else:
                        st.write("No flights found.")
        else:
            st.write("Please enter a prompt.")

if __name__ == "__main__":
    main()
