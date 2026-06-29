import os

def write_file(filename, cont):
    try:
        if not os.path.exists(filename):
            with open(filename, "w", encoding="utf-8") as f:
                f.write(cont)
            print(f"\nContent written to '{filename}' successfully.\n")
        else:
            with open(filename, "a", encoding="utf-8") as f:
                cont = "\n" + cont
                f.write(cont)
            print(f"\nContent added to file '{filename}' successfully.\n")
        return True
    except Exception as e:
        print(f"\nAn error occurred while writing to file '{filename}': {e}\n")
        return False

def read_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        print(f"\nFile '{filename}' not found.\n")
        return None
    except Exception as e:
        print(f"\nAn error occurred while reading file '{filename}': {e}\n")
        return None

def reverse_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        content_reversed = content[::-1]
        return content_reversed
    except FileNotFoundError:
        print(f"\nFile '{filename}' not found.\n")
        return None
    except Exception as e:
        print(f"\nAn error occurred while reversing file '{filename}': {e}\n")
        return None

def main():
    content = read_file("notes.txt")
    if content is not None:
        file1 = write_file("upper.txt", content.upper())
        file2 = write_file("lower.txt", content.lower())
        file3 = write_file("reverse.txt", reverse_file("lower.txt"))
        print("\nFiles created successfully.\n")
        print(f"Content of the reversed file:\n{read_file('reverse.txt')}\n")

if __name__ == "__main__":
    main()

