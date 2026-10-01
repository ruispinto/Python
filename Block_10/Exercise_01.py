import re
import datetime

if __name__ == "__main__":
    file_name = input() # asks for a log filename
    
    # if the file name is blank it will use a default file name
    if file_name.strip() == "": file_name = "c:\\tmp\\logs_mistos.log"

    # try to open the file and read its contents, if it fails it will print an error message
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()

    except (FileNotFoundError, OSError):
        print(f"Unable to open file: {file_name}")

    # in case of success opening the file...
    else:
        # iterate through each line in the file
        for line in lines:

            # this section checks if the line is a syslog entry and extracts the timestamp
            # syslog sample: 2024-11-04 03:22:11
            # regex to apply (not necessary): \b(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\b
            #syslog_log = re.search(r"\b(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\b", line)

            if syslog_log:
                
                # could use the regex group to extract the timestamp, but instead I will split the line and join the first two pieces to form the timestamp string
                #result = datetime.datetime.strptime(s.group(1),"%Y-%m-%d %H:%M:%S")

                splited_results = line.strip().split()
                new_result = splited_results[0] + " " + splited_results[1]

                result = datetime.datetime.strptime(new_result,"%Y-%m-%d %H:%M:%S")

                #continue   # usefull but not necessary

            
            # this section checks if the is an apache log entry and extracts the timestamp
            # apache sample: [04/Nov/2024:10:45:33 +0000]
            # regex to apply: \[(\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4})\]
            apache_log = re.search(r"\[(\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4})\]", line)
            if apache_log:
                result = datetime.datetime.strptime(apache_log.group(1),"%d/%b/%Y:%H:%M:%S %z")

            # print the result in the format YYYY-MM-DD HH:MM:SS
            print(result.strftime("%Y-%m-%d %H:%M:%S"))
