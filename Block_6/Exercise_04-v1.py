import random

def guess():
    global words
    words = ["banana", "pineapple", "apple", "cherry", "tomato", "passion fruit", "strawberry", "mango", "orange", "avocado"]
    return random.choice(words)

def main():
    computer = guess()
    word = letter = ""
    c = 0
    while True:
        c += 1
        print("\nGuess the fruit:")
        for li in words:
            if li == computer:
                print(li + "<")
            else:
                print(li)
        
        print("\nLetters: " + word)
        letter = input(f"\nWrite a letter to guess the fruit (or 'exit' to exit): ")
        if letter.lower() == "exit":
            print("Exiting the game...\n")
            break
        elif letter.lower() in computer:
            word += letter.lower()

        if word == computer:
            print(f"\nCongratulations! You guessed it... the fruit I thought of was {computer}")
            print(f"You only took {c} attempt(s)\n")
            break

if __name__ == "__main__":
    main()
