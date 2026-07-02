global dict

dict = {}

def show_scores():
    print("\nStudent's list:")
    for name, data in dict.items():
        print(
            f"Name: {name}, "
            f"Age: {data['Age']}, "
            f"Grade: {data['Grade']}"
        )
    return

def ask_data():
    name = input("\nName of the student (or 'exit'): ")
    age = input("Age: ")
    grade = input("Grade: ")
    return name, age, grade

def calc_scores():
    if not dict: return 0, 0, 0
    grades = [all_data["Grade"] for all_data in dict.values()]
    medium = sum(grades) / len(grades)
    return medium, max(grades), min(grades)

def add_item(n, i, v):
    dict[n] = {"Age": int(i),"Grade": float(v)}
    return

def main():
    while True:
        w, y, v = ask_data()
        if w.lower().strip() == "exit": break
        add_item(w, y, v)
        show_scores()
        medium, best_grade, worst_grade = calc_scores()
        print(f"\nMedium grades: {medium}")
        print(f"Best grade: {best_grade}")
        print(f"Worst grade: {worst_grade}")


if __name__ == "__main__":
    main()
    print("\n")

