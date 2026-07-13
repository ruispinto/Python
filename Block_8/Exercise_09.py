import re
 
def main():
    print("\nEmail validator")

    while True:
        user_input = input("\nWrite an email address (or 'exit'): ").strip()
        if user_input.lower() == "exit":
            return

        if type(user_input) == str:
            break
        else:
            print("\nEmail cannot be empty.")
            continue

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    #email_pattern = r"^[a-zA-Z0-9._%+-]+@(gmail.com|hotmail.com)$"
    if re.match(email_pattern, user_input):
        print("\nValid email address.\n")
    else:
        print("\nInvalid email address.\n")

if __name__ == "__main__":
    main()

