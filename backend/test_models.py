from google import genai

client = genai.Client(api_key="AQ.Ab8RN6ItljTC1PNfDJme5o4sLpSMYbtbtQgyRGzGlVypX1mHkQ")

for model in client.models.list():
    print(model.name)