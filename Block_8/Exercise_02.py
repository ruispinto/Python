import os

def read_file(fn, op):
    try:
        with open(fn, "r", encoding="utf-8") as f:
            content = f.read()
        if op == 1:
            return content.upper()
        elif op == 2:
            return content.lower()
        else:
            return content
    except FileNotFoundError:
        print(f"\nFile '{fn}' not found.\n")
        return None
    except Exception as e:
        print(f"\nAn error occurred while reading file '{fn}': {e}\n")
        return None

def main():
    #file_name = input("\nEnter the file name: ")
    file_name = "message.txt"
    print("\nFile content:\n")
    print("=" * 13)
    print(f"Upper case content:\n{read_file(file_name, 1)}\n")
    print("-" * 13)
    print(f"Lower case content:\n{read_file(file_name, 2)}\n")

if __name__ == "__main__":
    main()
