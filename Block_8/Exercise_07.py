from datetime import datetime, timedelta

def main():
    print("\nDate Calculator")

    while True:
        user_date = input("\nWrite a date in the format 'dd-mm-yyyy' (or 'exit'): ").strip()
        if user_date.lower() == "exit":
            break
        if not type(user_date) == str:
            print("Date cannot be empty or isn't in the asked format.")
            continue
        else:
            break

    day, month, year = map(int, user_date.split("-"))
    user_date = datetime(year, month, day)
    result = user_date - timedelta(days = 7)
    print(f"\nPast date was: {result.strftime('%d-%m-%Y')}\n")


if __name__ == "__main__":
    main()

