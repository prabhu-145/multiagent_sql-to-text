from services.llm_service import generate_response

prompt = "What is HER2 biomarker?"

response = generate_response(prompt)

print(response)