def menu():
    print("\nConverter")
    print("\n1. Decimal to binary")
    print("2. Binary to decimal")
    print("0. Exit")
    return

def calc_bin(n):
    if n == 0: return "0"
    if n > 0:
        b = ""
        while n > 0:
            r = n % 2
            b = str(r) + b
            n = n // 2
    return b

def calc_dec(n):
    d = e = 0
    while n != "":
        x = int(n[-1])
        d += x * (2 ** e)
        e += 1
        n = n[:-1]
    return d


def main():
    while True:
        menu()
        opt = input("\nChoose an option: ")
        try:
            if int(opt) == 1:
                print("\nDecimal to binary")
                num = input("Write a number (or 'exit' to exit): ")
                if num.lower() == "exit":
                    print("\n")
                    return
                result = calc_bin(int(num))
                print(f"\nBinary: {result}\n")
            elif int(opt) == 2:
                print("\nBinary to decimal")
                num = input("Write the number (or 'exit' to exit): ")
                if num.lower() == "exit":
                    print("\n")
                    return
                result = calc_dec(num)
                print(f"\nDecimal: {result}\n")
            elif int(opt) == 0:
                print("\n")
                return

        except:
            print("Invalid option!\n")
            continue
        

if __name__ == "__main__":
    main()

