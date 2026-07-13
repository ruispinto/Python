def printer(num):
    x = 1
    while x <= num:
        print(x)
        x += 1

def main():
    number = int(input("\nWrite a number: "))
    printer(number)
    print("\n")

if __name__ == "__main__":
    main()
    
