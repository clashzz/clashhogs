import datetime
import csv, pandas

MONTHS_MAPPINGS={
    1:"Jan", 2:"Feb", 3:"Mar",4:"Apr", 5:"May", 6:"Jun",7:"Jul", 8:"Aug", 9:"Sep",10:"Oct", 11:"Nov", 12:"Dec",
}
STANDARD_CREDITS={"cw_attack": 10, "cw_miss": -10, "cwl_attack": 10, "cwl_miss": -10,
                  "donation#1":30,"donation#2":20, "donation#3":10}
STANDARD_ATTACKUP_WEIGHTS={"u1":1.25, "u2":1.5, "u3":1.75}
STANDARD_ATTACKDOWN_WEIGHTS={"d1":0.75, "d2":0.5, "d3":0.25}

def summarise_by_townhalls(thlvl_attacks, thlvl_attackstars, writer=None):
    data_as_list=[]
    row_index=[]
    header = ["3 stars", "2 stars", "1 star", "0 star"]
    for thlvl in sorted(thlvl_attacks.keys()):
        total_attacks = thlvl_attacks[thlvl]
        star_freq = thlvl_attackstars[thlvl]

        star3 = 0
        star2 = 0
        star1 = 0
        star0 = 0

        if 3 in star_freq.keys():
            star3 = star_freq[3]
        if 2 in star_freq.keys():
            star2 = star_freq[2]
        if 1 in star_freq.keys():
            star1 = star_freq[1]
        if 0 in star_freq.keys():
            star0 = star_freq[0]

        row = ["TH" + str(thlvl), star3, star2, star1, star0, total_attacks]
        if writer is not None:
            writer.writerow(row)

        data_as_list.append(row[1:-1])
        row_index.append("TH" + str(thlvl))
    return data_as_list, row_index, header

def summarise_by_months(attacks:dict, writer=None):
    attacks_by_months ={}
    for t, atk in attacks.items():
        time=atk._time
        month = time.month
        if month in attacks_by_months.keys():
            data = attacks_by_months[month]
        else:
            data=[]
        data.append(atk)
        attacks_by_months[month]=data


    months = sorted(list(attacks_by_months.keys()))
    indeces = [MONTHS_MAPPINGS[m] for m in months]
    zerostars=[]
    onestars=[]
    twostars=[]
    threestars=[]

    for m in months:
        attacks = attacks_by_months[m]
        zeros=0
        ones=0
        twos=0
        threes=0
        for atk in attacks:
            if atk._stars ==0:
                zeros+=1
            elif atk._stars ==1:
                ones+=1
            elif atk._stars ==2:
                twos+=1
            elif atk._stars ==3:
                threes+=1
        zerostars.append(zeros)
        onestars.append(ones)
        twostars.append(twos)
        threestars.append(threes)

    df = pandas.DataFrame({'0 star': zerostars,
                       '1 star': onestars,
                        '2 stars':twostars,
                           '3 stars':threestars}, index=indeces)

    return df

def summarise_attacks(attacks: dict, thlvl_attacks:dict, thlvl_stars:dict):
    total_stars = 0
    total_attacks = 0
    for atk in attacks.values():
        if not atk._is_out:
            continue
        total_stars += atk._stars
        total_attacks += 1

        n = 1
        if atk._target_thlvl in thlvl_attacks.keys():
            n += thlvl_attacks[atk._target_thlvl]
        thlvl_attacks[atk._target_thlvl] = n

        s = atk._stars
        if atk._target_thlvl in thlvl_stars.keys():
            star_freq = thlvl_stars[atk._target_thlvl]
        else:
            star_freq = {}
        update_stats(star_freq, s)
        thlvl_stars[atk._target_thlvl] = star_freq

    return total_attacks, total_stars

def update_stats(star_freq: dict, stars: int):
    n = 1
    if stars in star_freq.keys():
        n += star_freq[stars]
    star_freq[stars] = n


class ClanWatch:
    def __init__(self, tag, name, guildid, guildname):
        self._tag=tag
        self._name=name
        self._guildid=guildid #discord guild id
        self._guildname=guildname
        self._creditwatch=True
        self._channel_warmiss=None #discord channel id for war missed attacks
        self._channel_warsummary=None #discord channel id for monthly war summary
        self._channel_clansummary=None #discord channel id for monthly clan feed summary
        self._creditwatch_points = STANDARD_CREDITS.copy()
        self._attackup_weights=STANDARD_ATTACKUP_WEIGHTS.copy()
        self._attackdown_weights=STANDARD_ATTACKDOWN_WEIGHTS.copy()

    def clear(self):
        self._creditwatch=True
        self._channel_warmiss=None #discord channel id for war missed attacks
        self._channel_warsummary=None #discord channel id for monthly war summary
        self._channel_clansummary=None #discord channel id for monthly clan feed summary
        self.reset_credits()
        self.reset_attackweights()

    def reset_credits(self):
        self._creditwatch_points = STANDARD_CREDITS.copy()

    def reset_attackweights(self):
        self._attackup_weights=STANDARD_ATTACKUP_WEIGHTS.copy()
        self._attackdown_weights=STANDARD_ATTACKDOWN_WEIGHTS.copy()

class Attack:
    # id = an arbitrary id
    # target_thlvl= town hall level of the target being attacked
    # target_thlvl= town hall level of the attacker
    # stars = #of stars won
    # is_outgoing: True indicating an attack; False indicating a defence.
    def __init__(self, id: str, target_thlvl: int, source_thlvl: int, stars: int, is_outgoing: bool,
                 time: datetime.datetime):
        self._id = id
        self._target_thlvl = target_thlvl
        self._source_thlvl = source_thlvl
        self._stars = stars
        self._is_out = is_outgoing
        self._time = time


class Player:
    # name: player name, as collected from sidekick discord war feed
    #
    def __init__(self, tag: str, name: str):
        self._tag = tag
        self._name = name
        self._unused_attacks = 0  # num of attacks this player had
        self._attacks = {}  # attacks used and associated data
        self._defences = []  # num of times this player is attacked

        self._total_stars = 0
        self._total_attacks = 0
        self._thlvl_attacks = {}
        self._thlvl_stars = {}

        self._data_populated = False

    def summarize_attacks(self):
        self._total_attacks, self._total_stars=summarise_attacks(self._attacks, self._thlvl_attacks, self._thlvl_stars)
        # thlvl_attacks = {}
        # thlvl_stars = {} #key=0/1/2/3 stars; value=frequency

        # for atk in self._attacks.values():
        #     if not atk._is_out:
        #         continue
        #     self._total_stars += atk._stars
        #     self._total_attacks += 1
        #
        #     n = 1
        #     if atk._target_thlvl in self._thlvl_attacks.keys():
        #         n += self._thlvl_attacks[atk._target_thlvl]
        #     self._thlvl_attacks[atk._target_thlvl] = n
        #
        #     s = atk._stars
        #     if atk._target_thlvl in self._thlvl_stars.keys():
        #         star_freq = self._thlvl_stars[atk._target_thlvl]
        #     else:
        #         star_freq = {}
        #     update_stats(star_freq, s)
        #     self._thlvl_stars[atk._target_thlvl] = star_freq

        # return total_stars, thlvl_attacks, thlvl_stars
        self._data_populated = True

class ClanWarData:
    # name: clan name, as collected from sidekick discord war feed
    #
    def __init__(self, tag: str):
        self._tag = tag
        self._players = []

        self._clan_total_attacks = 0
        self._clan_total_stars = 0
        self._clan_total_unused_attacks = 0
        self._clan_thlvl_attacks = {}
        self._clan_thlvl_attackstars = {}

        self._data_populated = False

    def summarize_attacks(self, outfolder=None):
        for p in self._players:
            if not p._data_populated:
                p.summarize_attacks()
            # self.output_player_war_data(outfolder, p)

            self._clan_total_unused_attacks += p._unused_attacks
            self._clan_total_attacks += p._total_attacks
            self._clan_total_stars += p._total_stars

            for k, v in p._thlvl_attacks.items():
                c_thlvl_attacks = v
                if k in self._clan_thlvl_attacks.keys():
                    c_thlvl_attacks += self._clan_thlvl_attacks[k]
                self._clan_thlvl_attacks[k] = c_thlvl_attacks

            for k, data in p._thlvl_stars.items():
                if k in self._clan_thlvl_attackstars.keys():
                    clan_data = self._clan_thlvl_attackstars[k]
                else:
                    clan_data = {}

                for star, freq in data.items():
                    if star in clan_data.keys():
                        clan_data[star] += freq
                    else:
                        clan_data[star] = freq

                self._clan_thlvl_attackstars[k] = clan_data

        self._data_populated = True

    def output_clan_war_data(self, out_csv: str):
        if not self._data_populated:
            self.summarize_attacks(out_csv)

        master_csv = out_csv + "/clan_war_data.csv"

        summary = {}

        # player overview
        with open(master_csv, 'w', newline='\n') as csvfile:
            writer = csv.writer(csvfile, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_ALL)
            writer.writerow(["Player Overview"])
            writer.writerow(["Player", "Total attacks", "Unused attacks", "Total stars", "Avg star per attack"])
            for p in self._players:
                if p._total_attacks == 0:
                    avg = 0
                else:
                    avg = round(p._total_stars / p._total_attacks, 1)
                writer.writerow([p._name, p._total_attacks, p._unused_attacks, p._total_stars,
                                 avg])
            writer.writerow(["\n"])

            # clan overview
            writer.writerow(["Clan Overview"])
            writer.writerow(["Total attacks", self._clan_total_attacks])
            writer.writerow(["Total unused attacks", self._clan_total_unused_attacks])
            writer.writerow(["Total stars", self._clan_total_stars])
            summary["Total attacks"] = self._clan_total_attacks
            summary["Total unused attacks"] = self._clan_total_unused_attacks
            summary["Total stars"] = self._clan_total_stars
            writer.writerow(["\n"])

            # prepare the data frame
            data_as_list, row_index, header=summarise_by_townhalls(self._clan_thlvl_attacks, self._clan_thlvl_attackstars, writer)
            writer.writerow(header)

        df = pandas.DataFrame(data_as_list, columns=header, index=row_index)
        return df, summary
