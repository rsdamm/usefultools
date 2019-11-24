
from datetime import datetime, timezone

def main():
    test_date()

def test_date():

    subject_line_dt = datetime.now()

    dt_string = subject_line_dt.strftime("%m/%d/%Y %H:%M")
    subject_line= "with no changes - " + dt_string
    print(subject_line)

    dt_string_local = subject_line_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)
    dt_string = dt_string_local.strftime("%m/%d/%Y %H:%M")
    subject_line = " with tz awareness - " + dt_string
    print(subject_line)

if __name__ == "__main__": main()