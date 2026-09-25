import re

if __name__ == "__main__":
    file_name = input()

    try:
        with open(file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()

    except (FileNotFoundError, OSError):
        print(f"Unable to open file: {file_name}")

    else:
        counter = {}

        for line in lines:
            if "ERROR" in line or "WARNING" in line:
                result = re.search(
                    r"\b\d{1,3}(?:\.\d{1,3}){3}\b",
                    line
                )

                if result:
                    ip = result.group()
                    counter[ip] = counter.get(ip, 0) + 1

        suspects = []

        for ip, qty in counter.items():
            if qty >= 3:
                suspects.append((qty, ip))

        suspects.sort(reverse=True)

        print("=== AUDIT REPORT ===")
        print(f"Total lines scanned: {len(lines)}")
        print()
        print("Suspect IPs (3 or more alerts ERROR/WARNING):")

        if not suspects:
            print("  (none)")
        else:
            for qty, ip in suspects:
                print(f"  {ip} - {qty} alerts")
