from google import genai
client = genai.Client(api_key='AIzaSyBOrW3GP6y02Fre00c_m5Ly2lwDvcBaKjs')
r = client.models.generate_content(model='gemini-2.0-flash', contents='Say hello')
print(r.text)