from openai import OpenAI
import os

# Define the code_writer_agent class
class CodeWriterAgent:
    def __init__(self):
        # Initialize the OpenAI client for LM Studio
        self.client = OpenAI(base_url="http://localhost:8000/v1", api_key="lm-studio")

    def create_completion(self, prompt, model="QuantFactory/Meta-Llama-3-8B-Instruct-GGUF"):
        # Create a completion request to the LM Studio
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant. Solve tasks using your coding and language skills. Use Python code or shell script as needed, and make sure the code is complete and ready to execute."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        # Access the content directly from the response
        return response.choices[0].message.content

# Example usage
def main():
    # Initialize the code_writer_agent
    agent = CodeWriterAgent()

    # Define a prompt for the agent
    prompt = """
    Provide Python code to perform the following tasks:
    1. Collect information by printing the current date and time.
    2. Create a file named 'example.txt' with a simple message.
    3. Read the content of 'example.txt' and print it.
    """

    # Get the completion from the agent
    response = agent.create_completion(prompt)
    print("Generated Code:\n", response)

if __name__ == "__main__":
    main()
