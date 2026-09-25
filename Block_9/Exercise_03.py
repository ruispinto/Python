import os
import re

f = "c:\\rp\\log_simulado.log"

ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
ip_list = []

def read_file(fn):
    try:
        with open(fn, "r", encoding="utf-8") as f:
            content = f.readlines()
            return content
    except FileNotFoundError:
        print(f"\nFile '{fn}' not found.\n")
        return None
    except Exception as e:
        print(f"\nAn error occurred while reading file '{fn}': {e}\n")
        return None

def main():
    while True:
        print("\nSimple Log file analyzer")
        file_name = input("\nEnter the name of the file to read (or type 'exit' to quit): ")
        if file_name.lower() == "exit":
            print("\nGoodbye\n")
            return
        elif file_name.strip() == "":
            file_name = f
            break
        else:
            break

    content = read_file(file_name)

    if content is None:
        print(f"\nFile '{file_name}' could not be read.\n")
        return

    lines = others = ips1 = ips2 = 0
    for line in content:
        lines += 1
        r1 = re.search(ip_pattern, line)
        if r1:
            ips1 += 1
            r = r1.group()
            if r in ip_list:
                ips2 += 1
            else:
                ip_list.append(r)
        else:
            others += 1

    print("\nSummary:")
    t1 = "Lines:".ljust(15)
    t6 = "IPs: ".ljust(15)
    t7 = f"from which {ips2} are repeated"
    t99 = "Unidentified:".ljust(15)
    if lines>0:
        print(f"{t1} {str(lines).rjust(5)} total")
    else:
        print(f"{t1} (file is empty)")

    if others>0:
        print(f"{t99} {str(others).rjust(5)} lines found")
    if ips1>0:
        if ips2>0:
            print(f"{t6} {str(ips2).rjust(5)} unique IP addresses in a total of {str(ips1)} lines found")
        else:
            print(f"{t6} {str(ips1).rjust(5)} lines found")
        print("\nList of found unique IP addresses:")
        for n in ip_list:
            print(f"{n}")
    print("\n")
    return

if __name__ == "__main__":
    main()

