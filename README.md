# usefultools
collection of useful tools

forecast 
1) go to google maps and get lat/long
2) create a cloudwatch event rule with a cron schedule and constant input lat/long/location
example:  {"latitude": "39.828043","longitude":"-105.478366","location":"Black Hawk"}

Then function will execute with lat/long obtained to get the grid of BOU/45,66
     https://api.weather.gov/points/39.828043,-105.478366
Then it submits URL to get forecast grid.
    https://api.weather.gov/gridpoints/BOU/45,66/forecast
Details at https://www.weather.gov/documentation/services-web-api