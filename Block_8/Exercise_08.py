from datetime import datetime

def main():
    print("\nDate Calculator")

    while True:
        user_date1 = input("\nWrite a date in the format 'dd-mm-yyyy' (or 'exit'): ").strip()
        if user_date1.lower() == "exit":
            return

        user_date2 = input("\nWrite a second date in the same format (or 'exit'): ").strip()
        if user_date2.lower() == "exit":
            return

        if not type(user_date1) == str or not type(user_date2) == str:
            print("Date cannot be empty or isn't in the asked format.")
            continue
        else:
            break

    date1 = datetime.strptime(user_date1, "%d-%m-%Y")
    date2 = datetime.strptime(user_date2, "%d-%m-%Y")
    result = date2 - date1
    print(f"\nDifference between the dates is: {result.days} days\n")


if __name__ == "__main__":
    main()


