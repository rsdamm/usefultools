import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import dateutil.tz
import urllib3
import json

# https://docs.aws.amazon.com/ses/latest/DeveloperGuide/send-using-sdk-python.html

def lambda_handler(event, context):
    #cannot be global or lambda will reuse for subsequent executions from same container
    v_htmlpage = ""
    weather_report_gend = False

    # get parameters for execution example format:  {  "latitude": "39.0", "longitude": "-105.0"", "location": "City State","timezone": "US/Pacify", "sender": "renee@plesba.com", "recipient_list": ["x@domain.com","y@domain.com"]
    v_latitude = get_latitude_from_event(event)
    v_longitude = get_longitude_from_event(event)
    v_location = get_location_from_event(event)
    v_timezone = get_timezone_from_event(event)
    v_sender = get_sender_from_event(event)
    v_recipient_list = get_recipient_list_from_event(event)

    v_tz = dateutil.tz.gettz(v_timezone)
    v_dt_string = datetime.now(v_tz).strftime("%m/%d/%Y %H:%M:%S")

    print ("Forecast for latitude/longitude " + str(v_latitude) + "," + str(v_longitude) + ": " + v_location + " for " + v_dt_string)

    #get the URL gridpoint - trying 5 times
    for i in range(5):
        v_url_gridpoint = get_gridpoints_url(v_latitude, v_longitude)

        if not v_url_gridpoint:
            print("Unable to get gridpoint for lat/long...Attempt #" + str(i) + " failed...retrying")
            time.sleep(30)
        else:
            break

    #retrieve and format weather report
    if not v_url_gridpoint:
        print("Unable to get gridpoint for lat/long...exceeded maximum attempts..aborting...")
    else:
        print("Received gridpoint for lat/long. Continuing...")
        for i in range(5):
            v_htmlpage = weather_report(v_url_gridpoint, v_location)
            if not v_htmlpage:
                print("Unable to generate weather forecast...Attempt #" + str(i) + " failed...retrying")
                time.sleep(30)
            else:
                weather_report_gend = True
                break

    if weather_report_gend:
        # print(v_htmlpage)
        send_email(v_htmlpage, v_location, weather_report_gend, v_dt_string, v_sender, v_recipient_list)
    else:
        print("Weather Report could not be generated. Exceeded maximum attempts...aborting...")
    return {
        'statusCode': 200,
        'body': v_htmlpage
    }
def get_latitude_from_event(p_event):
    if 'latitude' in p_event:
        v_latitude = p_event['latitude']
    else:
        raise Exception('ERROR: Latitude not provided')
    return v_latitude

def get_longitude_from_event(p_event):
    if 'longitude' in p_event:
        v_longitude = p_event['longitude']
    else:
        raise Exception('ERROR: Longitude not provided')
    return(v_longitude)

def get_location_from_event(p_event):
    if 'location' in p_event:
        v_location = p_event['location']
    else:
        raise Exception('ERROR: Location not provided')
    return v_location
    
def get_timezone_from_event(p_event):
    if 'timezone' in p_event:
        v_timezone = p_event['timezone']
    else:
        raise Exception('ERROR: Location not provided')
    return v_timezone

def get_sender_from_event(p_event):
    if 'sender' in p_event:
        v_sender = p_event['sender']
    else:
        raise Exception('ERROR: sender not provided')
    return v_sender

def get_recipient_list_from_event(p_event):
    if 'recipient_list' in p_event:
        v_recipient_list = p_event['recipient_list']
    else:
        raise Exception('ERROR: recipient list not provided')
    return v_recipient_list

def send_email(p_htmlpage, p_location, p_weather_report_gend, p_dt_string, p_sender, p_recipient_list):
    CONFIGURATION_SET = "ConfigSet"
    AWS_REGION = "us-west-2"
    v_location = p_location
    v_htmlpage = p_htmlpage
    v_weather_report_gend = p_weather_report_gend
    v_dt_string = p_dt_string
    v_sender = p_sender
    v_recipient_list = p_recipient_list

    if v_weather_report_gend:
        print("Forecast generated -> sending email")
        subject_line = v_location + " Forecast " + v_dt_string
    else:
        print("ERROR: Forecast was not generated -> sending error email")
        subject_line = v_location + " Forecast - problem encountered " + v_dt_string

    # The subject line for the email.
    SUBJECT = subject_line

    # The HTML body of the email.
    BODY_HTML = v_htmlpage

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = "text weather report)\r\n"

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses', region_name=AWS_REGION)

    for recipient in v_recipient_list:
        # Try to send the email.
        try:
            # Provide the contents of the email.
            response = client.send_email(
                Destination={
                    'ToAddresses': [
                        recipient,
                    ],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': CHARSET,
                            'Data': BODY_HTML,
                        },
                        'Text': {
                            'Charset': CHARSET,
                            'Data': BODY_TEXT,
                        },
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': SUBJECT,
                    },
                },
                Source=v_sender,
                # If you are not using a configuration set, comment or delete the
                # following line
                # ConfigurationSetName=CONFIGURATION_SET,
            )
            print ("Email recipient: " + recipient )
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("Email successfully sent. Message ID:"),
            print(response['MessageId'])

def get_max_wind(p_raw_wind_speed, p_wind_raw_direction):
    # wind comes in 2 forms:  7 mph and 6 to 19 mph. need to get last if range is provided.

    parsed_windspeed = p_raw_wind_speed.split(' ')
    max_wind_speed = parsed_windspeed[len(parsed_windspeed) - 2]

    formatted_wind = ""
    if int(max_wind_speed) >= 15:
        formatted_wind = "<br>" + "Wind: " + max_wind_speed + " mph " + p_wind_raw_direction
    return formatted_wind

def get_gridpoints_url(p_latitude, p_longitude):
    # provide lat/long in decimal format
    v_url_latlong = "https://api.weather.gov/points/" + str(p_latitude) + "," + str(p_longitude)
    print("URL to get gridpoint..." + v_url_latlong)

    user_agent = {'user-agent': 'reneeforecaster weather@plesba.com'}
    http = urllib3.PoolManager(10, headers=user_agent)

    for i in range(5):
        try:
            response = http.request("GET", v_url_latlong)
        except urllib3.exceptions.TimeoutError:
            print("Timeout exception on get request to get gridpoint")
            return False
        except urllib3.error.URLError as e:
            print("ERROR: Exception raised on get request to get gridpoint")
            print(e)
            return False

        print("WeatherAPI request for gridpoint got status code " + str(response.status) + " on attempt# "+ str(i))
        if response.status == 200:
            break
    # build url string that will get forecast --> https://api.weather.gov/gridpoints/BOU/45,66/forecast

    if response.status == 200:
        #data = response.json()
        data = json.loads(response.data.decode('utf-8'))
        v_url_gridpoint = data["properties"]["forecast"]
        print("URL for forecast..." + v_url_gridpoint)
    else:
        print("ERROR: Unable to get gridpoints URL..aborting")
        v_url_gridpoint = ""

    return v_url_gridpoint

def weather_report(p_url_gridpoint, p_location):
    print('building weather_report' + p_url_gridpoint + ' ' + p_location)
    v_location = p_location
    v_htmlpage = ""
    v_url_gridpoint = p_url_gridpoint

    user_agent = {'user-agent': 'forecaster weather@plesba.com'}
    http = urllib3.PoolManager(10, headers=user_agent)
    for i in range(5):
        try:
            response = http.request("GET", v_url_gridpoint)
        except urllib3.exceptions.TimeoutError:
            print("Timeout exception on get request")
            return False
        except urllib3.error.URLError  as e:
            print("ERROR: Exception raised on get request")
            print(e)
            return False
        print("WeatherAPI request for forecast got status code " + str({response.status}) + " on attempt# "+ str(i) +  " retrying...")
        if response.status == 200:
            break

    #format html page
    v_htmlpage = """<html><head><title>Forecast</title></head>"""
    v_htmlpage += "<body> <h2>" + v_location + " Forecast</h2> <hr/>"
    v_htmlpage += """<table border="1" width="645">"""

    #print(response.text)
    data = ""
    data = json.loads(response.data.decode('utf-8'))
    print('printing data in function weather_report')
    print(data)
    periods = data["properties"]["periods"]

    # build the table header for the forecast by day of week/AM/PM
    v_htmlpage += "<tr>"
    for i in periods:
        if i['isDaytime']:
            v_htmlpage += "<th>" + i['name'] + "</th>"

    v_htmlpage += "</tr>\n"

    # get the daytime information
    v_htmlpage += "<tr>"
    for i in periods:
        if i['isDaytime']:
            wind_info = get_max_wind(i['windSpeed'], i['windDirection'])
            v_htmlpage += "<td>" + "Hi " + str(i['temperature']) + "º" + "<br>" + i['shortForecast'] + wind_info + "</td>"

    v_htmlpage += "</tr>\n"

    # get the daytime icons
    v_htmlpage += "<tr>"
    for i in periods:
        if i['isDaytime']:
            v_htmlpage += "<td>" + "<img src=" + i['icon'] + "></td>"

    v_htmlpage += "</tr>\n"

    # get the evening information
    v_htmlpage += "<tr>"
    for i in periods:
        if not i['isDaytime']:
            wind_info = get_max_wind(i['windSpeed'], i['windDirection'])
            v_htmlpage += "<td>" + "Lo " + str(i['temperature']) + "º" + "<br>" + i['shortForecast'] + wind_info + "</td>"

    v_htmlpage += "</tr>\n"

    # get the evening icons
    v_htmlpage += "<tr>"
    for i in periods:
        if not i['isDaytime']:
            v_htmlpage += "<td>" + "<img src=" + i['icon'] + "></td>"

    #    v_htmlpage += "<td>" + str(i['temperature']) + "</td>"
    #    v_htmlpage += "<td>" + i['shortForecast'] + "</td>"
    #    v_htmlpage += "<td>" + "<img src=" + i['icon'] + "></td>"

    v_htmlpage += "</tr>\n"

    # now get detailed forecast
    v_htmlpage += """
</table>
<hr/>
"""

    # build the table for the detailed forecast by day of week/AM/PM
    v_htmlpage += "<h3>Detailed Forecast </h3> "
    v_htmlpage += """
    <table border="1" width="645">
    """
    for i in periods:
        v_htmlpage += "<tr><td style=""" + "font-weight:bold""" + ">"
        v_htmlpage += i['name'] + "</td> <td>" + i['detailedForecast'] + "</td></tr>"

    # finish up html string
    v_htmlpage += """
</body>
</html>
"""
    return v_htmlpage
v_event = {
    "latitude": "39.0",
    "longitude": "-105.0",
    "location": "Test CO"
}
v_context = None

if __name__ == "__main__":
    lambda_handler(v_event,v_context)
