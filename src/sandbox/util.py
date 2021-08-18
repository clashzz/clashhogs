import datetime

def parse_date(datestr:str):
    try:
        date=datetime.datetime.strptime(datestr, '%d/%m/%Y')
        return date
    except:
        return datetime.datetime.now()

def normalise_name(text):
    text = text.encode('ascii', 'ignore').decode("utf-8")
    return text.strip().replace(" ","_")

def value_found_in_text(text:str, values:list):
    for v in values:
        if v in text:
            return True
    return False