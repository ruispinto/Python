import re
from datetime import datetime

# declare the regular expressions for syslog, apache, ip addresses log formats as well as the timestamp log format
RE_SYSLOG = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\S+) ([^\s\[:]+)(?:\[[^\]]*\])?: ?(.*)$")
RE_APACHE = re.compile(r'^(\S+) \S+ \S+ \[([^\]]+)\] "([^"]*)" (\d{3})(?:\s|$)')
RE_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
DATE_FMT = "%Y-%m-%d %H:%M:%S"

if __name__ == "__main__":
    # get a file name from the user, or use a default file name if the user does not provide one
    file_name = "c:\\tmp\\logs_mistos.log"

    # open the file and read its contents into a list of lines, handling any errors that may occur
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()

    except (FileNotFoundError, OSError):
        print(f"Unable to open file: {file_name}")

    else:
        # print the header for the output table
        header = ("TIMESTAMP".ljust(19) + " | " + "level".ljust(7) + " | " + "service".ljust(7) + " | " + "IP".ljust(15) + " | " + "MESSAGE")
        print(header)
        print("-" * len(header))

        # initialize counters for syslog and apache entries
        syslog_counter = apache_counter = other_counter = 0

        # iterate through each line in the log file
        for line in lines:
            # strip any leading or trailing whitespace from the line
            line = line.strip()

            # check if the line matches the syslog format
            matchmaking = RE_SYSLOG.match(line)
            if matchmaking:
                # check if the timestamp is valid
                try:
                    datetime.strptime(matchmaking.group(1), DATE_FMT)
                except ValueError:
                    continue
                # extract the relevant information from the matched groups
                timestamp = matchmaking.group(1)
                level = matchmaking.group(2)
                service = matchmaking.group(3)
                message = matchmaking.group(4)
                ip_match = RE_IP.search(message)
                ip = ip_match.group() if ip_match else "N/A"
                # increment the syslog counter
                syslog_counter += 1
            else:
                # check if the line matches the apache format
                matchmaking = RE_APACHE.match(line)
                if not matchmaking:
                    # if the line does not match either format, increment the counter for other lines and skip to the next line
                    other_counter += 1
                    continue
                try:
                    dt = datetime.strptime(matchmaking.group(2), "%d/%b/%Y:%H:%M:%S %z")
                except ValueError:
                    continue
                
                # extract the relevant information from the matched groups
                timestamp = dt.strftime(DATE_FMT)
                err_class = int(matchmaking.group(4)) // 100
                if err_class in (2, 3):
                    level = "INFO"
                elif err_class == 4:
                    level = "WARNING"
                elif err_class == 5:
                    level = "ERROR"
                else:
                    continue
                ip = matchmaking.group(1)
                message = matchmaking.group(3)

                # set the service name to "apache" for apache log entries
                service = "apache"
                
                # increment the apache counter
                apache_counter += 1

            print(timestamp.ljust(19) + " | " + level.ljust(7) + " | " + service.ljust(7) + " | " + ip.ljust(15) + " | " + message)


        print(f"\nFound {syslog_counter} syslog entries, {apache_counter} apache entries, and {other_counter} other lines.")