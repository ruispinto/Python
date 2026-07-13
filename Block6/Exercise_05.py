def options_list(n1, n2):
    while n2 != 0:
        r = n1 % n2
        print(f"{n1} ÷ {n2} -> remainder = {r}")
        n1 = n2
        n2 = r
 
    return n1

def main():
    num1 = input("\nWrite a number (or 'exit' to exit): ")
    num2 = input("Write another number (or 'exit' to exit): ")
    if num1 < num2: num1, num2 = num2, num1
    result = options_list(int(num1), int(num2))
    print(f"\nThe greatest common divisor is {result}\n")

if __name__ == "__main__":
    main()
