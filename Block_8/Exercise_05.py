def ask_grades():
    while True:
        question = input("Grade: ").strip()
        try:
            grade = float(question.replace(",", "."))
            if grade.is_integer():
                grade = int(grade)
            return grade
        except ValueError:
            print("Please enter a valid grade.")


def save_classroom(students, file_name="classroom.txt"):
    if not students:
        print("\nNo student was registered.")
        return

    name_width = max(len("Name"), max(len(name) for name, _ in students))
    grade_width = max(len("Grade"), max(len(str(grade)) for _, grade in students))

    header = f"{'Name':<{name_width}} | {'Grade':<{grade_width}}"
    separator = "-" * len(header)

    lines = [header, separator]
    for name, grade in students:
        lines.append(f"{name:<{name_width}} | {str(grade):<{grade_width}}")

    with open(file_name, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nTable saved in '{file_name}' with {len(students)} student(s):\n")
    print("\n".join(lines))


def main():
    students = []
    print("Class registration (write 'exit' in the name to finish)")

    while True:
        name = input("\nName of the student (or 'exit'): ").strip()
        if name.lower() == "exit":
            break
        if not name:
            print("The name cannot be empty.")
            continue

        grade = ask_grades()
        students.append((name, grade))

    save_classroom(students)


if __name__ == "__main__":
    main()

