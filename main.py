# Mathos Favours Tracker

favours = []

def log_favour(person, description):
    favour = {
        "person": person,
        "description": description
    }
    favours.append(favour)
    print(f"Logged: {description} for {person}")

def show_favours():
    print("\nAll favours:")
    for favour in favours:
        print(f"- {favour['person']}: {favour['description']}")

log_favour("João", "Helped him move")
log_favour("Ana", "Called when she needed to talk")
log_favour("Mãe", "Fixed her laptop")

show_favours()