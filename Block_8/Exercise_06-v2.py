import datetime

def change_date(d):
    day, month, year = map(int, d.split())
    return f"{year:04d}/{month:02d}/{day:02d}"

def main():
    print("\nDate Format")

    while True:
        user_date = input("\nWrite a date in the format 'dd mm yyyy' (or 'exit'): ").strip()
        if user_date.lower() == "exit":
            break
        if not type(user_date) == str:
            print("Date cannot be empty or isn't in the asked format.")
            continue
        else:
            break

    if not user_date.lower() == "exit":
        result = change_date(user_date)
        print(f"\nThe date format is now 'yyyy/mm/dd': {result}\n")


if __name__ == "__main__":
    main()
