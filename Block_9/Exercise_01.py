import os
import requests

global dict, shopping_cart

# Portuguese VAT default tax is 23%
VAT_TAX = 23

# nif.pt free webservice, used to check if a VAT number actually exists.
# Request a free API key at: https://www.nif.pt/contactos/api/
# Leave as None to skip the online check and rely on local format validation only.
NIF_PT_API_KEY = None
NIF_PT_ENDPOINT = "https://www.nif.pt/"

# Valid first digit(s) for a Portuguese VAT number (simplified reference list)
VALID_NIF_PREFIXES = (
    "1", "2", "3", "45", "5", "6",
    "70", "71", "72", "74", "75", "77", "78", "79",
    "8", "90", "91", "98", "99",
)

# initialize the shopping cart as an empty dictionary
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
    print("4. Empty shopping cart")
    print("0. exit")
    return

def add_shopping_cart():
    while True:
        products_list()
        cod = input("\nProduct name to add (0 to exit): ")
        if cod == "0":
            break
        if cod in dict:
            qty = input("Quantity ")
            try:
                qty = int(qty)
                if qty <= 0:
                    qty = 1
            except:
                qty = 1
            
            # check if the product is already in the shopping cart, if it is, add the quantity to the existing quantity, otherwise add the product to the shopping cart with the quantity
            if cod in shopping_cart:
                a = shopping_cart[cod]
            else:
                a = 0
            
            # add the product to the shopping cart with the quantity
            shopping_cart[cod] = a + qty

    return

def msg_empty_shopping_cart():
    print("\nEmpty shopping cart\n")
    return

def empty_shopping_cart():
    shopping_cart.clear()
    print("\nShopping cart emptied\n")
    return

def view_shopping_cart(op):
    # always test if the shopping cart is empty, if it is, print a message and return to the menu
    if len(shopping_cart) <= 0:
        msg_empty_shopping_cart()
        return
    # get the name and vat number of the customer, if the vat number is empty, it will be set to 999999990 (portuguese vat number for none)
    if op == 2:
        name,vat = get_client_data()
        if (vat[0] in ["5", "6", "8"]) and (vat in ["999999990", "123456789"]):
            dsc_empr = True
        else:
            dsc_empr = False
    else:
        name = "Final Consumer"
        vat = "999999990"
        dsc_empr = False
    
    # starts adding the lines to print the shopping cart or receipt
    l = "+" + "-" * 67 + "+\n"
    if op == 1:
        t0 = "Shopping cart"
    else:
        t0 = "RECEIPT"
    l += "|" + " " * 67 + "|\n"
    l += f"| {t0.ljust(65)} |\n"
    l += "|" + " " * 67 + "|\n"
    l += "+" + "-" * 67 + "+\n"
    l += "|" + " " * 67 + "|\n"
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
        if dsc_empr:
            dsc = st * .1
        else:
            dsc = st * 0
        l += f"| {t6.ljust(65)} |\n"
    elif st >= 500.0:
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
    stf = f"{st:.2f}"
    l += f"| {t5.rjust(48)} | {str(stf).rjust(10)} Eur |\n"
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
            while True:
                vat = input("VAT Number: ")
                if vat == "":
                    vat = "999999990"
                    break
                if not validate_nif_format(vat):
                    print("Invalid VAT number (failed format/check digit validation). Please try again.\n")
                    continue
                if NIF_PT_API_KEY:
                    exists = check_nif_exists(vat, NIF_PT_API_KEY)
                    if exists is False:
                        print("This VAT number was not confirmed by nif.pt. Please check it.\n")
                        continue
                break
            break
    return name, vat

def print_receipt():
    # always test if the shopping cart is empty, if it is, print a message and return to the menu
    if len(shopping_cart) <= 0:
        msg_empty_shopping_cart()
        return
    
    # ask for the name and vat number to print the receipt
    name, vat, lines = view_shopping_cart(2)

    # test for the file name and write the receipt to a file
    file_name = "receipt.txt"
    if lines is None:
        msg_empty_shopping_cart()
        return
    # named the variable to file1 to avoid programming language conflicts
    file1 = write_file(file_name, lines)
    if file1:
        print("\nReceipt written to file 'receipt.txt' successfully.\n")
        print(lines)
    return

def write_file(filename, cont):
    # try to write the file, if it exists, append the content, otherwise create a new file
    try:
        if not os.path.exists(filename):
            with open(filename, "w", encoding="utf-8") as f:
                f.write(cont)
            # removed the following print statement to avoid printing success message
            #print(f"\nContent written to '{filename}' successfully.\n")
        else:
            with open(filename, "a", encoding="utf-8") as f:
                cont = "\n" + cont
                f.write(cont)
            # removed the following print statement to avoid printing success message
            #print(f"\nContent added to file '{filename}' successfully.\n")
        return True
    except Exception as e:
        # removed the following print statement to avoid printing error message
        #print(f"\nAn error occurred while writing to file '{filename}': {e}\n")
        return False

# function to validate the NIF format and check digit locally
def validate_nif_format(nif):
    # validates the NIF format and check digit locally
    # this does NOT confirm the NIF is registered, only that it is well-formed
    nif = nif.strip()

    if not nif.isdigit() or len(nif) != 9:
        return False

    if not nif.startswith(VALID_NIF_PREFIXES):
        return False

    total = sum(int(d) * w for d, w in zip(nif[:8], range(9, 1, -1)))
    remainder = total % 11
    check_digit = 0 if remainder < 2 else 11 - remainder

    return check_digit == int(nif[8])


def check_nif_exists(nif, api_key):
    # queries the nif.pt webservice to check if the NIF is actually registered
    # returns True / False, or None if the service could not be reached
    try:
        params = {"json": 1, "q": nif, "key": api_key}
        response = requests.get(NIF_PT_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return bool(data.get("nif_validation"))
    except requests.RequestException:
        # if the service is unreachable, don't block the user - just skip the online check
        return None


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
                print_receipt()
            elif opc == 4:
                empty_shopping_cart()
        except:
            continue
    print("\n")


if __name__ == "__main__":
    main()


