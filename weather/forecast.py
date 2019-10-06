from botocore.vendored  import requests
import boto3
from botocore.exceptions import ClientError
from datetime import datetime


#https://docs.aws.amazon.com/ses/latest/DeveloperGuide/send-using-sdk-python.html

htmlpage = """
<html><head><title>Rangeview Forecast</title></head>
<body>
<h2>Rangeview Forecast </h2>
<hr/>
<table border="1">
<tr><th>Day</th><th>Temp</th><th>Forecast</th><th>Icon</th></tr>
"""
def main():
    weather_report()
    print(htmlpage)
    send_email(htmlpage)

def lambda_handler(event, context):
    weather_report()
    send_email(htmlpage)
    return {
        'statusCode': 200,
        'body': htmlpage
    }

def send_email(htmlpage):
    SENDER = "test@test.com"
    RECIPIENT = "testto@test.com"
    CONFIGURATION_SET = "ConfigSet"
    AWS_REGION = "us-west-2"

    now = datetime.now()

    dt_string = now.strftime("%m/%d/%Y %H:%M")
    subject_line= "Rangeview Weather Report - " + dt_string

    # The subject line for the email.
    SUBJECT = subject_line

    # The HTML body of the email.
    BODY_HTML = htmlpage

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = "text weather report)\r\n"


    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=AWS_REGION)

    # Try to send the email.
    try:
        #Provide the contents of the email.
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
            #ConfigurationSetName=CONFIGURATION_SET,
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])

def weather_report():
    global htmlpage

    url = "https://api.weather.gov/gridpoints/BOU/45,66/forecast"

    response = requests.request("GET", url)

    #print(response.text)
    data = response.json()

    periods = data["properties"]["periods"]
    #print(len(periods))


    htmlpage += "<tr>"

    for i in periods:
        if i['isDaytime']:
            htmlpage += "<td>" + i['name'] + "<br>" + "Hi " + str(i['temperature']) + "º" + "<br>" + i['shortForecast'] +"</td>"

    #    htmlpage += "<td>" + str(i['temperature']) + "</td>"
    #    htmlpage += "<td>" + i['shortForecast'] + "</td>"
    #    htmlpage += "<td>" + "<img src=" + i['icon'] + "></td>"

    htmlpage += "</tr>\n"

    for i in periods:
        if i['isDaytime']:
            htmlpage += "<td>" + "<img src=" + i['icon'] + "></td>"
    #    htmlpage += "<td>" + str(i['temperature']) + "</td>"
    #    htmlpage += "<td>" + i['shortForecast'] + "</td>"
    #    htmlpage += "<td>" + "<img src=" + i['icon'] + "></td>"

    htmlpage += "</tr>\n"


    for i in periods:
        if not i['isDaytime']:
            htmlpage += "<td>" + "Lo " + str(i['temperature']) + "º" + "<br>" + i['shortForecast'] + "</td>"

    #    htmlpage += "<td>" + str(i['temperature']) + "</td>"
    #    htmlpage += "<td>" + i['shortForecast'] + "</td>"
    #    htmlpage += "<td>" + "<img src=" + i['icon'] + "></td>"

    htmlpage += "</tr>\n"

    for i in periods:
        if not i['isDaytime']:
            htmlpage += "<td>" + "<img src=" + i['icon'] + "></td>"
    #    htmlpage += "<td>" + str(i['temperature']) + "</td>"
    #    htmlpage += "<td>" + i['shortForecast'] + "</td>"
    #    htmlpage += "<td>" + "<img src=" + i['icon'] + "></td>"

    htmlpage += "</tr>\n"

    #for i in periods:
    #    htmlpage += "<tr>"
    #    htmlpage += "<td>" + i['name'] + "</td>"
    #    htmlpage += "<td>" + str(i['temperature']) + "</td>"
    #    htmlpage += "<td>" + i['shortForecast'] + "</td>"
    #    htmlpage += "<td>" + "<img src=" + i['icon'] + "></td>"
    #   htmlpage += "</tr>\n"
    #htmlpage += """
    #</table>
    #</body>
    #</html>
    #"""



    htmlpage += """
</table>
</body>
</html>
"""

if __name__ == "__main__": main()