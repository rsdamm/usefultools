import requests

url = "https://api.weather.gov/gridpoints/BOU/45,66/forecast"

response = requests.request("GET", url)

#print(response.text)
data = response.json()

periods = data['properties']['periods']
print(len(periods))

for i in periods:
        print(i['shortForecast'])
