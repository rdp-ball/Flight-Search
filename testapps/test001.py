# app.py
import streamlit as st
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from amadeu import search_flights

# Load the pre-trained model and tokenizer from Hugging Face
model_name = "distilgpt2"
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

# Function to generate a response from the LLM
def generate_response(prompt):
    inputs = tokenizer.encode(prompt, return_tensors="pt")
    outputs = model.generate(inputs, max_length=150, num_return_sequences=1)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

# Streamlit app setup
st.title("Chatbot with Amadeus API Integration")

# Sidebar for Amadeus API interaction
st.sidebar.header("Flight Search Parameters")
origin = st.sidebar.text_input("Origin Location Code", value="MIA")
destination = st.sidebar.text_input("Destination Location Code", value="ATL")
departure_date = st.sidebar.date_input("Departure Date", value="2024-11-01").strftime('%Y-%m-%d')
adults = st.sidebar.number_input("Number of Adults", min_value=1, max_value=10, value=1)

if st.sidebar.button("Search Flights"):
    with st.spinner("Searching for flights..."):
        flight_data = search_flights(origin, destination, departure_date, adults)
        st.success("Search complete!")
        st.json(flight_data)

# Chatbot interface
st.header("Chat with the bot")
if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.text_input("You: ", key="user_input")

if user_input:
    st.session_state.messages.append(("user", user_input))
    
    # Special command to search flights
    if user_input.startswith("search flights"):
        with st.spinner("Searching for flights..."):
            origin, destination, date = "MIA", "ATL", "2024-11-01"  # Default values for the example
            flight_data = search_flights(origin, destination, date, adults=1)
            response = f"Here are the flight details: {flight_data}"
    else:
        response = generate_response(user_input)
    
    st.session_state.messages.append(("bot", response))
    st.experimental_rerun()

for role, msg in st.session_state.messages:
    if role == "user":
        st.write(f"You: {msg}")
    else:
        st.write(f"Bot: {msg}")
