import streamlit as st
from amadeus import Client, ResponseError
from openai import OpenAI
import json
import re
import ast

# Initialize the Amadeus client
amadeus = Client(
     client_id='8zAQaOrWiKQnWpS1W5dAoGKyApdr2zmH',
    client_secret='4dZJVCV22xIwROU7'
)

# Initialize OpenAI client
client = OpenAI(base_url="http://localhost:8000/v1", api_key="lm-studio")

def extract_dict_from_message(message):
    try:
        match = re.search(r'\{.*?\}', message, re.DOTALL)
        if match:
            dict_str = match.group(0)
            extracted_dict = ast.literal_eval(dict_str)
            print("Extracted dictionary:", extracted_dict)  # Debug: check extracted dictionary
            return extracted_dict
        else:
            print("No dictionary found in the message.")
            return None
    except (SyntaxError, ValueError) as e:
        print(f"Error extracting dictionary: {e}")
        return None

def convert_prompt_to_parameters(prompt):
    response = client.chat.completions.create(
        model="QuantFactory/Meta-Llama-3-8B-Instruct-GGUF",
        messages=[
            {"role": "system", "content": '''Convert the following natural language prompt into parameters for an Amadeus API hotel search.
            Example format:
            {
                "city_code": "PAR",
                "check_in_date": "2024-08-04",
                "check_out_date": "2024-08-07",
                "adults": 1
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
            "city_code": parameters.get('city_code', '').upper(),
            "check_in_date": parameters.get('check_in_date', '').strip(),
            "check_out_date": parameters.get('check_out_date', '').strip(),
            "adults": parameters.get('adults', 1)
        }
        
        for key in ['city_code', 'check_in_date', 'check_out_date']:
            if not cleaned_parameters[key]:
                st.error(f"Missing required parameter: {key}")
                return {}
        
        return cleaned_parameters
    else:
        st.error("Failed to extract parameters from the response.")
        return {}

def search_hotels(city_code, check_in_date, check_out_date, adults=1):
    try:
        # Print parameters for debugging
        st.write(f"Searching hotels with parameters: city_code={city_code}, check_in_date={check_in_date}, check_out_date={check_out_date}, adults={adults}")
        
        response = amadeus.shopping.hotel_offers_search.get(
            cityCode=city_code,
            checkInDate=check_in_date,
            checkOutDate=check_out_date,
            adults=adults
        )
        st.write("Response Data:", response.data)
        return response.data
    except ResponseError as error:
        st.error(f"Amadeus API Error: {error}")
        return str(error)

def main():
    st.title('Travel Search App')

    # Input field for natural language prompt
    prompt = st.text_area('Enter your travel search query')

    if st.button('Search'):
        if prompt:
            if 'hotel' in prompt.lower():
                # Convert prompt to parameters for hotel search
                parameters = convert_prompt_to_parameters(prompt)
                
                if parameters:
                    # Extract parameters
                    city_code = parameters.get('city_code', 'N/A')
                    check_in_date = parameters.get('check_in_date', 'N/A')
                    check_out_date = parameters.get('check_out_date', 'N/A')
                    adults = int(parameters.get('adults', 1))
                    
                    # Call the search_hotels function
                    result = search_hotels(city_code, check_in_date, check_out_date, adults)
                    
                    if isinstance(result, str):  # In case of an error
                        st.error(result)
                    else:
                        # Display relevant data
                        st.write("### Hotel Results:")
                        if isinstance(result, list):
                            for offer in result:
                                hotel_id = offer.get('id', 'N/A')
                                hotel_name = offer.get('hotel', {}).get('name', 'N/A')
                                price = offer.get('offers', [{}])[0].get('price', {}).get('total', 'N/A')
                                check_in = offer.get('offers', [{}])[0].get('checkInDate', 'N/A')
                                check_out = offer.get('offers', [{}])[0].get('checkOutDate', 'N/A')

                                st.write(f"Hotel ID: {hotel_id}")
                                st.write(f"Hotel Name: {hotel_name}")
                                st.write(f"Price: {price}")
                                st.write(f"Check-In Date: {check_in}")
                                st.write(f"Check-Out Date: {check_out}")
                                st.write("---")
                        else:
                            st.write("No hotels found.")
            else:
                st.write("Please specify a flight or hotel search.")
        else:
            st.write("Please enter a prompt.")

if __name__ == "__main__":
    main()