global dict

dict = {}

def show_scores():
    print("\nStudents:")
    for nome, dados in dict.items():
        print(
            f"Name: {nome}, "
            f"Age: {dados['Age']}, "
            f"Grade: {dados['Grade']}"
        )
    return

def ask_data():
    nome = input("\nName of the student (or 'exit'): ")
    idade = input("Age: ")
    valor = input("Grade: ")
    return nome, idade, valor

def calc_scores():
    if not dict: return 0, 0, 0
    notas = [dados["Grade"] for dados in dict.values()]
    return max(notas)

def add_item(n, i, v):
    dict[n] = {"Age": int(i),"Grade": float(v)}
    return

def main():
    while True:
        w, y, v = ask_data()
        if w.lower().strip() == "exit": break
        add_item(w, y, v)
        show_scores()
        best_grade = calc_scores()
        print(f"Best grade: {best_grade}\n")


if __name__ == "__main__":
    main()


