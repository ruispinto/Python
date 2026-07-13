stk_mngmt = {}


def menu():
    print("\nStock management")
    print("\n1. Add items")
    print("2. Delete items")
    print("3. Add stock")
    print("4. Sales")
    print("0. Exit")
    return


def stock():
    print("\nCurrent stock:")
    if not stk_mngmt:
        print("(empty)")
    else:
        for name, qty in stk_mngmt.items():
            warning = "  -> LOW STOCK!" if qty < 5 else ""
            print(f"  {name}: {qty}{warning}")
    return


def ask_quantity(message):
    while True:
        val = input(message)
        if val.lower() == "exit":
            return None
        try:
            qty = int(val)
            if qty < 0:
                print("The quantity cannot be negative.")
                continue
            return qty
        except ValueError:
            print("Please write a valid number.")


def warn_low_stk(name):
    if stk_mngmt[name] < 5:
        print(f"WARNING: stock of '{name}' is very low (only {stk_mngmt[name]} units remaining)!")


def add_item():
    stock()
    name = input("\nWrite the name of the new item (or 'exit' to quit): ")
    if name.lower() == "exit":
        return
    if name in stk_mngmt:
        print(f"The item '{name}' already exists. Use 'Add stock' to increase the quantity.")
        return
    qty = ask_quantity("Write the initial quantity: ")
    if qty is None:
        return
    stk_mngmt[name] = qty
    print(f"Item '{name}' added with {qty} units.")
    warn_low_stk(name)


def delete_item():
    stock()
    name = input("\nWrite the name of the item to delete (or 'exit' to quit): ")
    if name.lower() == "exit":
        return
    if name not in stk_mngmt:
        print(f"The item '{name}' does not exist.")
        return
    stk_mngmt.pop(name)
    print(f"\nItem '{name}' removed.\n")


def add_stk():
    stock()
    name = input("\nWrite the name of the item (or 'exit' to quit): ")
    if name.lower() == "exit":
        return
    if name not in stk_mngmt:
        print(f"The item '{name}' does not exist. Use 'Add items' first.")
        return
    qty = ask_quantity("How many units do you want to add? ")
    if qty is None:
        return
    stk_mngmt[name] += qty
    print(f"Stock updated: '{name}' now has {stk_mngmt[name]} units.")


def sell():
    stock()
    name = input("\nWrite the name of the item sold (or 'exit' to quit): ")
    if name.lower() == "exit":
        return
    if name not in stk_mngmt:
        print(f"The item '{name}' does not exist.")
        return
    qty = ask_quantity("How many units were sold? ")
    if qty is None:
        return
    if qty > stk_mngmt[name]:
        print(f"\nNot enough stock! Only {stk_mngmt[name]} units available.\n")
        return
    stk_mngmt[name] -= qty
    print(f"\nSale recorded: '{name}' now has {stk_mngmt[name]} units.\n")
    warn_low_stk(name)


def main():
    while True:
        menu()
        opt = input("\nChoose an option: ")
        try:
            opt = int(opt)
        except ValueError:
            print("Invalid option!\n")
            continue

        if opt == 1:
            add_item()
        elif opt == 2:
            delete_item()
        elif opt == 3:
            add_stk()
        elif opt == 4:
            sell()
        elif opt == 0:
            print("\nSee you next time!\n")
            return
        else:
            print("Invalid option!\n")


if __name__ == "__main__":
    main()
