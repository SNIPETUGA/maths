# Mathos - favour tracker

favours = []

def log_favour():
    person = input("Who did you do it for? ")
    description = input("What did you do? ")
    favour = {
        "person": person,
        "description": description
    }
    favours.append(favour)
    print(f"\nLogged: {description} for {person}\n")

def show_favours():
    if len(favours) == 0:
        print("\nNo favours logged yet.\n")
    else:
        print("\nAll favours:")
        for favour in favours:
            print(f"- {favour['person']}: {favour['description']}")
        print()

while True:
    print("1. Log a favour")
    print("2. See all favours")
    print("3. Quit")
    choice = input("Choose: ")

    if choice == "1":
        log_favour()
    elif choice == "2":
        show_favours()
    elif choice == "3":
        break
    else:
        print("Please choose 1, 2 or 3\n")