import re
from datetime import datetime


if __name__ == "__main__":
    file_name = "c:\\tmp\\logs_mistos.log"

    brute_force = {}
    scanning = {}
    at_dawn = {}

    try:
        with open(file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()

    except (FileNotFoundError, OSError):
        #a = Exception(FileNotFoundError)
        pass

    else:
        for line in lines:
            pieces = line.strip().split()

            if not pieces:
                continue

            # syslog
            if len(pieces) >= 5 and re.match(r"^\d{4}-\d{2}-\d{2}$", pieces[0]):

                try:
                    time_stamp = datetime.strptime(pieces[0] + " " + pieces[1], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue

                severity_degree = pieces[2]
                message = " ".join(pieces[4:])

                if "Failed password" in line:
                    ip_search = re.search(r"Failed password.*?\bfrom\s+(\d{1,3}(?:\.\d{1,3}){3})\b", line)

                    if ip_search:
                        ip = ip_search.group(1)
                        brute_force[ip] = brute_force.get(ip, 0) + 1

                if time_stamp.hour in range(0, 6):
                    if severity_degree == "ERROR":
                        ip_combo = re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", line)

                        if ip_combo:
                            ip = ip_combo.group()
                            at_dawn.setdefault(ip, []).append(("ERROR", time_stamp.strftime("%H:%M:%S")))

                    elif severity_degree == "WARNING":
                        ip_combo = re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", line)

                        if ip_combo:
                            ip = ip_combo.group()
                            at_dawn.setdefault(ip, []).append(("WARNING", time_stamp.strftime("%H:%M:%S")))

            # apache
            elif len(pieces) >= 7 and pieces[3].startswith("["):

                ip = pieces[0]
                try:
                    time_stamp = datetime.strptime(pieces[3][1:] + " " + pieces[4][:-1], "%d/%b/%Y:%H:%M:%S %z")
                except ValueError:
                    continue

                try:
                    err_code = int(pieces[-2])
                except ValueError:
                    continue

                if err_code >= 400 and err_code <= 599:
                    scanning[ip] = scanning.get(ip, 0) + 1

                if time_stamp.hour in range(0, 6):
                    if err_code >= 400 and err_code <= 499:
                        severity_degree = "WARNING"
                    elif err_code >= 500 and err_code <= 599:
                        severity_degree = "ERROR"
                    else:
                        severity_degree = None

                    if severity_degree is not None:
                        at_dawn.setdefault(ip, []).append((severity_degree, time_stamp.strftime("%H:%M:%S")))

        for ip, quantity in brute_force.items():
            if quantity >= 5:
                print(f"BRUTE_FORCE {ip} {quantity}")

        for ip, quantity in scanning.items():
            if quantity >= 4:
                print(f"SCANNING {ip} {quantity}")

        for ip, evnts in at_dawn.items():
            for severity_degree, ts_hour in evnts:
                if severity_degree == "ERROR":
                    print(f"CRITICAL {ip} {ts_hour}")
                elif severity_degree == "WARNING":
                    print(f"SUSPICIOUS {ip} {ts_hour}")

        ips = set(brute_force) | set(scanning) | set(at_dawn)

        for ip in ips:
            criteria = []

            if brute_force.get(ip, 0) >= 5:
                criteria.append("bruteforce")

            if scanning.get(ip, 0) >= 4:
                criteria.append("scanning")

            if ip in at_dawn:
                criteria.append("at dawn")

            if len(criteria) >= 2:
                print(f"HIGHLY_SUSPICIOUS {ip} {' '.join(criteria)}")