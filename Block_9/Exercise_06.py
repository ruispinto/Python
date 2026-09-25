import re

file_name = "c:\log_simulado 1.log"

try:
    with open(file_name, "r", encoding="utf-8") as f:
        lines = f.readlines()

except (FileNotFoundError, OSError):
    print(f"Unable to open file: {file_name}")
else:
    counter = {}
    count_hours = {}

    count_lines = 1
    for line in lines:
        parts = line.split()

        level = parts[2]

        result = re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", line)

        if result:
            ip = result.group()

            if level in ("ERROR", "WARNING"):
                counter[ip] = counter.get(ip, 0) + 1

            if level == "ERROR":
                hour = int(parts[1].split(":")[0])

                if 0 <= hour < 6:
                    count_hours[ip] = count_hours.get(ip, 0) + 1

        count_lines += 1

    suspects = []

    for ip, qty in counter.items():
        if qty >= 3:
            suspects.append((qty, ip))

    highly_suspects = []

    for ip, qty in count_hours.items():
        highly_suspects.append((qty, ip))

    suspects.sort(reverse=True)
    highly_suspects.sort(reverse=True)

    print("=== AUDIT LOG REPORT ===")
    print(f"Total lines scanned: {len(lines)}")
    print()
    print("Suspect IPs (3 or more alerts ERROR/WARNING):")

    if not suspects:
        print("  (none)")
    else:
        for qty, ip in suspects:
            print(f"  {ip} - {qty} alerts")

    print()
    print("Highly Suspect IPs (errors between 00:00 and 06:00):")

    if not highly_suspects:
        print("  (none)")
    else:
        for qty, ip in highly_suspects:
            print(f"  {ip} - {qty} early-morning errors")

