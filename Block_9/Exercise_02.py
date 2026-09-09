import os
import re

error_pattern = r"error"
warning_pattern = r"warning"
info_pattern = r"info"
debug_pattern = r"debug"

def read_file(fn):
    try:
        with open(fn, "r", encoding="utf-8") as f:
            content = f.readlines(-1)
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
            print("\nProgram ended\n")
            return
        else:
            break

    content = read_file(file_name)

    if content is None:
        print(f"\nFile '{file_name}' could not be read.\n")
        return

    errors = warnings = infos = debugs = lines = others = 0
    for line in range(len(content)):
        lines += 1
        if re.search(error_pattern, content[line], re.IGNORECASE):
            errors += 1
        elif re.search(warning_pattern, content[line], re.IGNORECASE):
            warnings += 1
        elif re.search(info_pattern, content[line], re.IGNORECASE):
            infos += 1
        elif re.search(debug_pattern, content[line], re.IGNORECASE):
            debugs += 1
        else:
            others += 1

    print("\nSummary:")
    t1 = "Lines:".ljust(15)
    t2 = "Errors:".ljust(15)
    t3 = "Warnings:".ljust(15)
    t4 = "Info:".ljust(15)
    t5 = "Debug:".ljust(15)
    t6 = "Unidentified:".ljust(15)
    if lines>0:
        print(f"{t1} {str(lines).rjust(5)} total")
    else:
        print(f"{t1} (file is empty)")

    if errors>0:
        print(f"{t2} {str(errors).rjust(5)} lines found")
    if warnings>0:
        print(f"{t3} {str(warnings).rjust(5)} lines found")
    if infos>0:
        print(f"{t2} {str(errors).rjust(5)} lines found")
    if warnings>0:
        print(f"{t3} {str(warnings).rjust(5)} lines found")
    if infos>0:
        print(f"{t4} {str(infos).rjust(5)} lines found")
    if debugs>0:
        print(f"{t5} {str(debugs).rjust(5)} lines found")
    if others>0:
        print(f"{t6} {str(others).rjust(5)} lines found")
    print("\n")
    return

if __name__ == "__main__":
    main()

