from botocore.vendored import requests
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone

# https://docs.aws.amazon.com/ses/latest/DeveloperGuide/send-using-sdk-python.html

htmlpage = """
<html><head><title>Forecast</title></head>
"""


def lambda_handler(event, context):
    weather_report_gend = False

    # get parameters for execution {"latitude": "39.828043","longitude":"-105.478366","location":"Black Hawk"}
    if 'latitude' in event:
        v_latitude = event['latitude']
    else:
        raise Exception('Latitude not provided')
    if 'longitude' in event:
        v_longitude = event['longitude']
    else:
        raise Exception('Longitude not provided')
    if 'location' in event:
        v_location = event['location']
    else:
        raise Exception('Location not provided')

    for i in range(5):
        weather_report_gend = weather_report(v_latitude, v_longitude, v_location)
        if weather_report_gend:
            break
        else:
            print("Unable to generate weather forecast...retrying")
            time.sleep(60)

    if weather_report_gend:
        # print(htmlpage)
        send_email(htmlpage, v_location)
    else:
        print("Weather Report could not be generated")
    return {
        'statusCode': 200,
        'body': htmlpage
    }


def send_email(htmlpage, p_location):
    SENDER = "x@x.com"
    RECIPIENT = "x@x.com"
    CONFIGURATION_SET = "ConfigSet"
    AWS_REGION = "us-west-2"
    v_location = p_location

    subject_line_dt = datetime.now()

    # dt_string = subject_line_dt.strftime("%m/%d/%Y %H:%M")

    dt_string_local = subject_line_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)
    dt_string = dt_string_local.strftime("%m/%d/%Y %H:%M")
    subject_line = v_location + " Forecast "

    # The subject line for the email.
    SUBJECT = subject_line

    # The HTML body of the email.
    BODY_HTML = htmlpage

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = "text weather report)\r\n"

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses', region_name=AWS_REGION)

    # Try to send the email.
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
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
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
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
    v_url = "https://api.weather.gov/points/" + str(p_latitude) + "," + str(p_longitude)

    try:
        response = requests.request("GET", v_url)
    except requests.exceptions.Timeout:
        print("Timeout exception on get request to get gridpoint")
        return False
    except requests.exceptions.RequestException as e:
        print("Exception raised on get request to get gridpoint")
        print(e)
        return False

    # print(response.text)
    # build url string that will get forecast --> https://api.weather.gov/gridpoints/BOU/45,66/forecast

    data = response.json()

    v_url = data["properties"]["forecast"]

    print("url for forecast...")
    print(v_url)

    return v_url


def weather_report(p_latitude, p_longitude, p_location):
    global htmlpage

    v_latitude = p_latitude
    v_longitude = p_longitude
    v_location = p_location

    url = get_gridpoints_url(v_latitude, v_longitude)

    try:
        response = requests.request("GET", url)
    except requests.exceptions.Timeout:
        print("Timeout exception on get request")
        return False
    except requests.exceptions.RequestException as e:
        print("Exception raised on get request")
        print(e)
        return False


    htmlpage += "<body> <h2>" + v_location + " Forecast</h2> <hr/>"
    htmlpage += """<table border="1" width="645">"""

    # print(response.text)

    data = response.json()

    periods = data["properties"]["periods"]

    # build the table header for the forecast by day of week/AM/PM
    htmlpage += "<tr>"
    for i in periods:
        if i['isDaytime']:
            htmlpage += "<th>" + i['name'] + "</th>"

    htmlpage += "</tr>\n"

    # get the daytime information
    htmlpage += "<tr>"
    for i in periods:
        if i['isDaytime']:
            wind_info = get_max_wind(i['windSpeed'], i['windDirection'])
            htmlpage += "<td>" + "Hi " + str(i['temperature']) + "º" + "<br>" + i['shortForecast'] + wind_info + "</td>"

    htmlpage += "</tr>\n"

    # get the daytime icons
    htmlpage += "<tr>"
    for i in periods:
        if i['isDaytime']:
            htmlpage += "<td>" + "<img src=" + i['icon'] + "></td>"

    htmlpage += "</tr>\n"

    # get the evening information
    htmlpage += "<tr>"
    for i in periods:
        if not i['isDaytime']:
            wind_info = get_max_wind(i['windSpeed'], i['windDirection'])
            htmlpage += "<td>" + "Lo " + str(i['temperature']) + "º" + "<br>" + i['shortForecast'] + wind_info + "</td>"

    htmlpage += "</tr>\n"

    # get the evening icons
    htmlpage += "<tr>"
    for i in periods:
        if not i['isDaytime']:
            htmlpage += "<td>" + "<img src=" + i['icon'] + "></td>"

    #    htmlpage += "<td>" + str(i['temperature']) + "</td>"
    #    htmlpage += "<td>" + i['shortForecast'] + "</td>"
    #    htmlpage += "<td>" + "<img src=" + i['icon'] + "></td>"

    htmlpage += "</tr>\n"

    # now get detailed forecast
    htmlpage += """
</table>
<hr/>
"""

    # build the table for the detailed forecast by day of week/AM/PM
    htmlpage += "<h3>Detailed Forecast </h3> "
    htmlpage += """
    <table border="1" width="645"> 
    """
    for i in periods:
        htmlpage += "<tr><td style=""" + "font-weight:bold""" + ">"
        htmlpage += i['name'] + "</td> <td>" + i['detailedForecast'] + "</td></tr>"

    # finish up html string
    htmlpage += """
</body>
</html>
"""
    return True


if __name__ == "__main__": main()
