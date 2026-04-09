import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate


# Load environment variables from .env file
load_dotenv()

# Get the Google API key from environment variables
google_api_key = os.getenv("GOOGLE_API_KEY")

if not google_api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment variables or .env file.")

# Initialize the Google Generative AI LLM
# You can choose a model like "gemini-1.0-pro"
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=google_api_key)

# List models
# models = llm.listModels()
# print("Available models:", models)

# Create a simple prompt template
# prompt = ChatPromptTemplate.from_messages([
#     ("system", "You are a helpful AI assistant."),
#     ("user", "{input}")
# ])
# Define a PromptTemplate with a variable 'question'
prompt = PromptTemplate.from_template("You are a helpful AI assistant. Answer: {question}")



# Create a simple chain
chain = prompt | llm

# Invoke the chain
print("Invoking the chain...")
#response = chain.invoke({"input": "What is the capital of France?"})
response = chain.invoke({"question": "What is the capital of France?"})

print("\n--- Response ---")
print(response.content)
print("\nEnvironment setup successful!!!")