
GRADE_POINTS = {
    'O': 10,
    'A': 9,
    'A+': 8,
    'B': 7,
    'B+': 6,
    'C': 5,
    'U': 0
}

def get_grade_input():
    """Gets and validates grade and credit inputs from the user."""
    while True:
        try:
            num_courses = int(input("Enter the number of courses: "))
            if num_courses > 0:
                break
            else:
                print("Please enter a positive number of courses.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    courses = []
    for i in range(num_courses):
        while True:
            grade = input(f"Enter grade for course {i+1} (O, A, A+, B, B+, C, U): ").upper()
            if grade in GRADE_POINTS:
                break
            else:
                print(f"Invalid grade: {grade}. Please choose from {list(GRADE_POINTS.keys())}")

        while True:
            try:
                credits = int(input(f"Enter credits for course {i+1}: "))
                if credits > 0:
                    break
                else:
                    print("Credits must be a positive number.")
            except ValueError:
                print("Invalid input. Please enter a number for credits.")
        courses.append({'grade': grade, 'credits': credits})
    return courses

def calculate_gpa(courses):
    """Calculates the GPA for a list of courses."""
    total_points = 0
    total_credits = 0
    for course in courses:
        total_points += GRADE_POINTS[course['grade']] * course['credits']
        total_credits += course['credits']

    return total_points / total_credits if total_credits > 0 else 0

def main():
    """Main function to run the GPA/CGPA calculator."""
    all_semesters_courses = []

    while True:
        print("\n--- GPA & CGPA Calculator ---")
        print("1. Calculate GPA for a semester")
        print("2. Calculate CGPA")
        print("3. Exit")

        choice = input("Enter your choice (1-3): ")

        if choice == '1':
            print("\nEntering courses for a new semester...")
            semester_courses = get_grade_input()
            all_semesters_courses.append(semester_courses)
            gpa = calculate_gpa(semester_courses)
            print(f"\nYour GPA for this semester is: {gpa:.2f}")

        elif choice == '2':
            if not all_semesters_courses:
                print("\nNo semester data found. Please calculate GPA for at least one semester first.")
                continue

            print("\nDo you want to add a new semester for CGPA calculation? (yes/no)")
            add_new = input("> ").lower()
            if add_new == 'yes':
                semester_courses = get_grade_input()
                all_semesters_courses.append(semester_courses)

            # Flatten the list of lists into a single list of courses
            all_courses = [course for semester in all_semesters_courses for course in semester]
            cgpa = calculate_gpa(all_courses)
            print(f"\nYour CGPA is: {cgpa:.2f}")

        elif choice == '3':
            print("Exiting the calculator. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 3.")

if __name__ == "__main__":
    main()
