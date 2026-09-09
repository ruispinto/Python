import os

global dict, shopping_cart

VAT_TAX = 23
shopping_cart = {}

dict = {
    "samsung monitor": 199.99,
    "huawei smartphone": 433.99,
    "lg tv": 590.99,
    "robot aspirador": 239.99,
    "samsung tv": 390.99,
    "samsung smartphone": 359.99,
    "iphone 15": 880.3,
    "iphone 15 pro": 970.99,
    "iphone 15 cover": 53.99
}

def products_list():
    l = "\nProducts list:\n"
    l += "+" + "-" * 29 + "+" + "-" * 14 + "+\n"
    for a,b in dict.items():
        b = f"{b:.2f}"
        l +=f"| {a.ljust(27)} | {str(b).rjust(8)} Eur |\n"
    l += "+" + "-" * 29 + "+" + "-" * 14 + "+\n"
    l += f"Prices are subject to VAT Tax at the legal rate ({VAT_TAX} %)"
    print(l)
    return

def menu():
    print("\n1. Add products to shopping cart")
    print("2. View shopping cart")
    print("3. Finalize purchase")
    print("0. exit")
    return

def add_shopping_cart():
    while True:
        products_list()
        cod = input("\nProduct name to add (0 to exit): ")
        if cod == "0":
            break
        if cod in dict:
            qtd = input("Quantity ")
            try:
                qtd = int(qtd)
            except:
                qtd = 1
            
            if cod in shopping_cart or len(shopping_cart) :
                a = shopping_cart[cod]
            else:
                a = 0
            
            shopping_cart[cod] = a + qtd
            #shopping_cart[cod] = qtd

    return

def empty_shopping_cart():
    print("\nEmpty shopping cart\n")
    return

def view_shopping_cart(op):
    if len(shopping_cart) <= 0:
        empty_shopping_cart()
        return
    name,vat = get_client_data()
    if (vat[0] == 5 or vat[0] == 6 or vat[0] == 8) and (not vat == "999999990" or not vat == "123456789"):
        dsc_empr = True
    else:
        dsc_empr = False
    
    l = "+" + "-" * 67 + "+\n"
    if op == 1:
        t0 = "Shopping cart"
    else:
        t0 = "RECEIPT"
    l += "|" + " " * 67 + "|\n"
    l += f"| {t0.ljust(65)} |\n"
    l += "|" + " " * 67 + "|\n"
    l += "+" + "-" * 67 + "+\n"
    t0 = "Name: " + name
    l += f"| {t0.ljust(65)} |\n"
    t0 = "Vat number: " + vat
    l += f"| {t0.ljust(65)} |\n"
    l += "|" + " " * 67 + "|\n"

    l += "+" + "-" * 29 + "+" + "-" * 14 + "+" + "-" * 5 + "+" + "-" * 16 + "+\n"
    t1 = "Product"
    t2 = "Unit Price"
    t3 = "Qty"
    t4 = "Total"
    t5 = "Special discount of 2% for values above 500 Eur"
    t6 = "Offer of a night at a hotel from the Pestana Group"
    l += f"| {t1.ljust(27)} | {t2.ljust(12)} | {t3.ljust(3)} | {t4.ljust(14)} |\n"
    l += "+" + "-" * 29 + "+" + "-" * 14 + "+" + "-" * 5 + "+" + "-" * 16 + "+\n"
    st = 0.0
    for a,b in shopping_cart.items():
        c = f"{dict[a]:.2f}"
        d = f"{dict[a]*b:.2f}"
        st += dict[a]*b
        l +=f"| {a.ljust(27)} | {str(c).rjust(8)} Eur | {str(b).rjust(3)} | {str(d).rjust(10)} Eur |\n"

    if st >= 800.0:
        e = 1
        f = 0
        if dsc_empr:
            dsc = st * .1
        else:
            dsc = st * 0
        l += f"| {t6.ljust(65)} |\n"
    elif st >= 500.0:
        e = 1
        f = 0
        if dsc_empr:
            dsc = st * .1
        else:
            dsc = st * .02
        l += f"| {t5.ljust(65)} |\n"
    
    l += "+" + "-" * 29 + "+" + "-" * 14 + "+" + "-" * 5 + "+" + "-" * 16 + "+\n"
    t5 = "Sub-total"
    t5a = "Discount to apply"
    t5b = "Sub-total with discount"
    t6 = "VAT Tax at " + str(VAT_TAX) + "%"
    t7 = "Total of shopping cart (with VAT Tax)"
    l += f"| {t5.rjust(48)} | {str(st).rjust(10)} Eur |\n"
    if dsc > 0:
        dscf = f"{dsc:.2f}"
        stcd = st - dsc
        stcdf = f"{stcd:.2f}"
        l += f"| {t5a.rjust(48)} | {str(dscf).rjust(10)} Eur |\n"
        l += "+" + "-" * 50 + "+" + "-" * 16 + "+\n"
        l += f"| {t5b.rjust(48)} | {str(stcdf).rjust(10)} Eur |\n"
        sti = float(stcd * (VAT_TAX / 100))
        ti = stcd + sti
    else:
        sti = float(st * (VAT_TAX / 100))
        ti = st + sti
    st1 = f"{st:.2f}"
    stif = f"{sti:.2f}"
    tif = f"{ti:.2f}"
    l += f"| {t6.rjust(48)} | {str(stif).rjust(10)} Eur |\n"
    l += f"| {t7.rjust(48)} | {str(tif).rjust(10)} Eur |\n"
    l += "+" + "-" * 29 + "+" + "-" * 14 + "+" + "-" * 5 + "+" + "-" * 16 + "+\n"
    return name,vat, l

def get_client_data():
    while True:
        name = input("\nCustomer name ('exit' to return to the menu): ")
        if name is None or len(name.strip()) == 0:
            print("Name too short\n")
            continue
        elif name == "exit":
            return
        else:
            vat = input("VAT Number: ")
            if vat == "":
                vat = "999999990"
            break
    return name, vat

def close_deal():
    if len(shopping_cart) <= 0:
        empty_shopping_cart()
        return
    
    name, vat, lines = view_shopping_cart(2)
    if (vat[0] == 5 or vat[0] == 6 or vat[0] == 8) and (not vat == "999999990" or not vat == "123456789"):
        dsc_empr = True
    else:
        dsc_empr = False
   
    file_name = "receipt.txt"
    if lines is None:
        empty_shopping_cart()
        return
    file1 = write_file(file_name, lines)
    if file1:
        print(lines)
    return

def write_file(filename, cont):
    try:
        if not os.path.exists(filename):
            with open(filename, "w", encoding="utf-8") as f:
                f.write(cont)
            #print(f"\nContent written to '{filename}' successfully.\n")
        else:
            with open(filename, "a", encoding="utf-8") as f:
                cont = "\n" + cont
                f.write(cont)
            #print(f"\nContent added to file '{filename}' successfully.\n")
        return True
    except Exception as e:
        #print(f"\nAn error occurred while writing to file '{filename}': {e}\n")
        return False


def main():
    while True:
        print("\nWelcome to the new online store of Electronics World")
        menu()
        opc = input("\nChoose an option ")
        try:
            opc = int(opc)
            if opc == 0:
                break
            elif opc == 1:
                add_shopping_cart()
            elif opc == 2:
                name, vat, lines = view_shopping_cart(1)
                print(lines)
            elif opc == 3:
                close_deal()
        except:
            continue
    print("\n")


if __name__ == "__main__":
    main()


