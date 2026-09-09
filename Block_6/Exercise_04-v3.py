import random

def guess():
    words = ["banana", "pineapple", "apple", "cherry", "tomato", "passion fruit", "strawberry", "mango", "orange", "avocado"]
    return random.choice(words)

def main():
    computer = guess()
    letter = ""
    word = ["_"] * len(computer)
    c = 0
    while "_" in word:
        c += 1
        print("\nGuess the fruit")
        # Here we use join to display the underscores separated by spaces
        print(" ".join(word))
        letter = input(f"\nWrite a letter to guess the fruit (or 'exit' to exit): ")
        if letter.casefold() == "exit":
            print("Exiting the game...\n")
            break
        elif letter.casefold() in computer:
            for i in range(len(computer)):
                if computer[i] == letter:
                    word[i] = letter

    # Show the complete word at the end
    print(" ".join(word))
    print(f"\nCongratulations! You guessed it... the fruit I thought of was {computer}")
    print(f"You only took {c} attempt(s)\n")

if __name__ == "__main__":
    main()