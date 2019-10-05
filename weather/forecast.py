import requests


url = "https://api.weather.gov/gridpoints/BOU/45,66/forecast"

response = requests.request("GET", url)

#print(response.text)
data = response.json()

periods = data["properties"]["periods"]
#print(len(periods))

htmlpage = """
<html><head><title>Rangeview Forecast</title></head>
<body>
<h2>Rangeview Forecast</h2>
<hr/>
<table border="1">
<tr><th>HighTemp</th><th>LowTemp</th><th>PrecipChance</th><th>Descrip</th></tr>
"""

for i in periods:
    htmlpage += "<tr>"
    htmlpage += "<td>" + i['name'] + "</td>"
    htmlpage += "<td>" + str(i['temperature']) + "</td>"
    htmlpage += "<td>" + i['shortForecast'] + "</td>"
    htmlpage += "<td>" + "<img src=" + i['icon'] + "></td>"
    htmlpage += "</tr>\n"

htmlpage += """
</table>
</body>
</html>
"""


print(htmlpage)