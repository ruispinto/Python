global dict

def show_dict(d):
    print("\n", d)
    return

def main():
    dict = {}
    while True:
        show_dict(dict)
        word = input("\nWrite a word (or 'exit'): ")
        if word.lower() == "exit":
            print("\n")
            quit()
        if len(word.strip()) < 2: print("\nWord too short\n")

        # Get a value from the user
        value = input("Write a value: ")
        if len(value) < 1: value = "-"

        dict.update({word: value})
    

if __name__ == "__main__":
    main()
