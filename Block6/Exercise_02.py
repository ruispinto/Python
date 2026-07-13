def sum_result():
    sv = 0
    x = 0
    while sv <= 1000:
        x += 1
        sv += x
    return x

def main():
    result = sum_result()
    print(f"\nThe highest value below or equal to 1000 is {result}\n")

if __name__ == "__main__":
    main()
    
