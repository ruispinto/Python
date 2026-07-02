global dict

dict = {}

def menu():
    print("\nDictionary")
    print("\n1. Add data")
    print("2. Delete data")
    print("3. Show data")
    print("0. Exit")
    return

def show_dict():
    print("\n")
    print(dict)
    return

def ask_data():
    show_dict()
    word = input("\nWrite a word (or 'exit' to exit): ")
    value = input("Write a value: ")
    return word, value


def add_item(t, v):
    return dict.update({t: v})

def remove_item(t):
    return dict.pop(t)

def main():
    while True:
        menu()
        option = input("\nChoose an option: ")
        try:
            if int(option) == 1:
                print("\nAdd data")
                w, v = ask_data()
                add_item(w, v)
            elif int(option) == 2:
                print("\nDelete data")
                show_dict()
                num = input("\nWrite the type (or 'exit' to exit): ")
                if num.lower() == "exit":
                    print("\n")
                    return
                remove_item(num)
            elif int(option) == 3:
                print("\nShow data")
                show_dict()
            elif int(option) == 0:
                print("\n")
                return

        except:
            print("Invalid option!\n")
            continue
        

if __name__ == "__main__":
    main()


