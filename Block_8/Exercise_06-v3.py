import datetime
import locale

locale.setlocale(locale.LC_ALL, 'pt_PT.UTF-8')

def convert_date(d):
    date_str = datetime.datetime.strptime(d, "%d %m %y")
    return date_str.strftime("%y/%m/%d")

if __name__ == "__main__":
    date_str = input("\nEnter a date in the format 'dd mm yy': ")
    converted_date = convert_date(date_str.strip())
    print(f"\nThe date format is now 'yyyy/mm/dd': {converted_date}")
    print(f"The date format is now 'yyyy/mm/dd': {datetime.datetime.strptime(date_str.strip(), '%d %m %y').strftime('%Y/%m/%d')}\n")
