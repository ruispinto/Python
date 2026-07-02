def sum_all(*args):
    total = 0
    for n in args:
        total += n
    return total
 
if __name__ == "__main__":
    print(sum_all(1, 2, 3, 4))
    print(sum_all(10, 20, 10, 15, 15))

