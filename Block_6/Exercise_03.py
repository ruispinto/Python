import random

def guess():
    return random.randint(0, 100)

def main():
    computer = guess()
    c = 0
    while True:
        c += 1
        num = input(f"\nWrite a number up to 100 (or 'exit' to exit): ")
        if num.lower() == "exit":
            print("Exiting the game...\n")
            break
        elif int(num) == computer:
            print(f"\nCongratulations! You guessed it... the number I thought of was {num}")
            print(f"You only took {c} attempt(s)\n")
            break
        elif int(num) < computer:
            print("\nThe secret number has to be larger")
        elif int(num) > computer:
            print("\nThe secret number has to be smaller")

if __name__ == "__main__":
    main()
