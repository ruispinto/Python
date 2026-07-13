import random

def guess():
    print("\nWelcome to the guessing game!")
    print("Try to guess the number I chose between 0 and 100.")
    return random.randint(0, 100)

def guessed(n,c):
    if n == c:
        print(f"\nCongratulations! You guessed it... the number I thought of was {c}")
        return True
    elif n < c:
        print("\nThe secret number has to be larger")
        return False
    elif n > c:
        print("\nThe secret number has to be smaller")
        return False
    else:
        return False

def main():
    computer = guess()
    c = 0
    while True:
        c += 1
        try:
            num = input(f"\nWrite a number up to 100 (or 'exit' to exit): ")
            if num.lower() == "exit":
                print("\nExiting the game...\n")
                break
            elif int(num) < 0 or int(num) > 100:
                print("\nThe number has to be between 0 and 100.\n")
                continue

            if (guessed(int(num), computer)):
                print(f"You only took {c} attempt(s)\n")
                computer = guess()
        except:
            print("\nPlease write a valid number, or 'exit'.\n")
            continue


if __name__ == "__main__":
    main()
