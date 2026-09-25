import os
import re
from operator import itemgetter

ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
ip_list = {}

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

def selected_second_character(word):
    return word[1]

def main():
    #while True:
        #print("\nSimple Log file analyzer")
        #file_name = input("\nEnter the name of the file to read (or type 'exit' to quit): ")
    file_name = input()
        #if file_name.lower() == "exit":
        #    #print("\nGoodbye...\n")
        #    return
        #else:
        #    break

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
            #print(r)
            if r in ip_list:
                ips2 += 1
                ip_list[r] += 1
            else:
                ip_list[r] = 1
        else:
            others += 1

    # print("\nSummary:")
    # t1 = "Lines:".ljust(15)
    # t6 = "IPs: ".ljust(15)
    # t7 = f"from which {ips2} are repeated"
    # t99 = "Unidentified:".ljust(15)
    # if lines>0:
    #     print(f"{t1} {str(lines).rjust(5)} total")
    # else:
    #     print(f"{t1} (file is empty)")

    # if others>0:
    #     print(f"{t99} {str(others).rjust(5)} lines found")
    if ips1>0:
        # if ips2>0:
        #     print(f"{t6} {str(ips2).rjust(5)} unique IP addresses in a total of {str(ips1)} lines found")
        # else:
        #     print(f"{t6} {str(ips1).rjust(5)} lines found")
        #print("\nList of found unique IP addresses:")
        sorted_ips = sorted(ip_list.items(), key=itemgetter(1), reverse=True)
        for ip,qty in sorted_ips:
            #print(f"{ip} - {qty} time(s)")
            print(f"{ip} {qty}")
    print("\n")
    return

if __name__ == "__main__":
    main()

