import re
from datetime import datetime

if __name__ == "__main__":
    file_name = input()
    if file_name.strip() == "": file_name = "c:\\tmp\\logs_mistos.log"

    try:
        with open(file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()

    except (FileNotFoundError, OSError):
        print(f"Unable to open file: {file_name}")

    else:
        # initialize counters for syslog and apache entries
        syslog_counter = apache_counter = 0
        # iterate through each line in the log file
        for line in lines:
            # split the line into pieces based on whitespace
            pieces = line.strip().split()

            # Syslog
            # checks for the '-' in the date format (YYYY-MM-DD) to identify syslog entries)
            if pieces[0].count("-") == 2:
                # get date and time from the first two pieces of the line and join them to form a timestamp string
                time_stamp = pieces[0] + " " + pieces[1]
                # get the severity code from the third piece of the line
                severity_code = pieces[2]
                # convert the timestamp string to a datetime object
                date_time = datetime.strptime(time_stamp, "%Y-%m-%d %H:%M:%S")
                # increment the syslog counter
                syslog_counter += 1

            # Apache
            else:
                # get the message code from the second-to-last piece of the line
                msg_code = int(pieces[-2])

                # determine the severity code based on the message code
                if 200 <= msg_code <= 399:
                    severity_code = "INFO"
                elif 400 <= msg_code <= 499:
                    severity_code = "WARNING"
                elif 500 <= msg_code <= 599:
                    severity_code = "ERROR"

                # get the timestamp from the fourth and fifth pieces of the line, remove the brackets, and join them to form a timestamp string
                time_stamp = pieces[3][1:] + " " + pieces[4][:-1]
                date_time = datetime.strptime(time_stamp, "%d/%b/%Y:%H:%M:%S %z")
                # increment the apache counter
                apache_counter += 1

            # print the timestamp and severity code in the specified format
            print(date_time.strftime("%Y-%m-%d %H:%M:%S") + " | " + severity_code)

        # print the total number of syslog and apache entries found (not necessary for the exercise, but useful for debugging)
        print(f"Found {syslog_counter} syslog entries and {apache_counter} apache entries.")
