import discord

MONTHS_MAPPINGS={
    1:"Jan", 2:"Feb", 3:"Mar",4:"Apr", 5:"May", 6:"Jun",7:"Jul", 8:"Aug", 9:"Sep",10:"Oct", 11:"Nov", 12:"Dec",
}

def load_properties(file):
    params={}
    with open(file) as f:
        lines = f.readlines()
        for l in lines:
            values = l.split("=")
            if len(values)<2:
                continue
            params[values[0].strip()]=values[1].strip()
    return params


def normalise_name(text):
    text = text.encode('ascii', 'ignore').decode("utf-8")
    return text.strip().replace(" ","_")

#letter O > number 0
def normalise_player_tag(tag):
    return tag.replace("O","0").upper()

def value_found_in_text(text:str, values:list):
    for v in values:
        if v in text:
            return True
    return False

def find_first_appearance(text:str, keywords:list):
    index=len(text)
    found=False
    for k in keywords:
        if k in text:
            found = True
            idx = text.index(k)
            if idx<index:
                index=idx
    if found:
        return index
    else:
        return -1

def embed_warnings(clan:str):
    embedVar = discord.Embed(title="Current warning records", description="Clan: {}".format(clan)) #, color=0x00ff00
    embedVar.add_field(name="01", value="DSE\nZZ\n0.5\n21-Nov-2021 19:05:32", inline=False)
    embedVar.add_field(name="02", value="DSE\nZZ\n0.5\n21-Nov-2021 20:05:32",inline=False)
    embedVar.add_field(name="04", value="DS\nZZ.mini\n0.5\n21-Nov-2021 19:05:32",inline=False)
    return embedVar