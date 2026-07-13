global stk_mngmnt
global warn_stk_lvl

stk_mngmnt = {}
warn_stk_lvl = 5


def menu():
    print("\nStock management")
    print("\n1. Add items")
    print("2. Delete items")
    print("3. Add stock")
    print("--------------------")
    print("4. Sales")
    print("0. Exit")
    return


def show_dict():
    print("\n")
    print(stk_mngmnt)
    return


def ask_data():
    show_dict()
    name = input("\nWrite an item name (or 'exit' to quit): ")
    stk = input("Write the initial stock level: ")
    return name, stk


def ask_qty(msg):
    while True:
        ask_data = input(msg)
        if ask_data.lower() == "exit":
            return None
        try:
            qty = int(ask_data)
            if qty < 0:
                print("The quantity cannot be negative.")
                continue
            return qty
        except ValueError:
            print("Please write a valid number.")
 

def add_item(n, s):
    return stk_mngmnt.update({n: s})


def remove_item(n):
    return stk_mngmnt.pop(n)


def sell():
    show_dict()
    name = input("\nWrite the name of the item sold (or 'exit' to quit): ")
    if name.lower() == "exit":
        return
    if name not in stk_mngmnt:
        print(f"The item '{name}' does not exist.")
        return
    qty = ask_qty("How many units were sold? ")
    if qty is None:
        return
    if qty > stk_mngmnt[name]:
        print(f"Not enough stock! Only {stk_mngmnt[name]} units available.")
        return
    stk_mngmnt[name] -= qty
    print(f"Sale registered: '{name}' now has {stk_mngmnt[name]} units.")
    warn_low_stk(name)
 

def warn_low_stk(name):
    if stk_mngmnt[name] < warn_stk_lvl:
        print("\nWarning: stock is low!")
        print(f"{name} has {stk_mngmnt[name]} units in stock!\n")
 

def main():
    while True:
        menu()
        opt = input("\nChoose an option: ")
        try:
            if int(opt) == 1:
                print("\nAdd items")
                w, v = ask_data()
                add_item(w, v)
            elif int(opt) == 2:
                print("\nDelete items")
                show_dict()
                num = input("\nWrite the item name to delete (or 'exit' to quit): ")
                if num.lower() == "exit":
                    print("\n")
                    return
                remove_item(num)
            elif int(opt) == 3:
                print("\nAdd stock")
                w, v = ask_qty()
            elif int(opt) == 0:
                print("\n")
                return

        except:
            print("Invalid option!\n")
            continue
        

if __name__ == "__main__":
    main()


