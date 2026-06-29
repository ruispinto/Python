import os

def write_file(file_name, cont):
    try:
        if not os.path.exists(file_name):
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(cont)
            print(f"\nContent written to file '{file_name}' successfully.\n")
        else:
            with open(file_name, "a", encoding="utf-8") as f:
                cont = "\n" + cont
                f.write(cont)
            print(f"\nContent added to file '{file_name}' successfully.\n")
        return True
    except Exception as e:
        print(f"\nAn error occurred while writing to file '{file_name}': {e}\n")
        return False

def read_file(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        print(f"\nFile '{file_name}' not found.\n")
        return None
    except Exception as e:
        print(f"\nAn error occurred while reading file '{file_name}': {e}\n")
        return None

def main():
    content = input("\nEnter the content to write to the file: ")
    valid = write_file("notes.txt", content)
    if valid:
        print("\nFile created successfully.\n")
        print(f"Content of the file:\n{read_file('notes.txt')}\n")

if __name__ == "__main__":
    main()

