import math
from re import search
 
contacts = {}
 
def add():
    Name = input("Name: ")
    Phone = input("Phone: ")
    contacts[Name] = Phone
    print(f"{Name} added")
 
def delete():
    print(contacts)
    Name = input("Name to remove: ")
    contacts.pop(Name)
    print(f"{Name} removed successfully")
 
def search():
    Name = input("Name to search: ")
    for name in contacts:    
        if Name in name:        
            print(f"Found: {name} - {contacts[name]}")
 
def main():
    while True:
        print("\n1. Add Phone")
        print("2. Remove Phone")
        print("3. Search Contacts")
        print("5. Show Contacts")
        print("4. Exit")
        opt = (input("Choose: "))
       
        if opt == "1":
            add()
        elif opt == "2":
            delete()
        elif opt == "3":
            search()
        elif opt == "4":
            print("\n")
            break
        elif opt == "5":
            print(contacts)
        else:
            print("\nInvalid option\n")
 
if __name__ == "__main__":
    main()
 
