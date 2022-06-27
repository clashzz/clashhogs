import datetime


# x = datetime.datetime(2022, 6, 27)
# y = datetime.datetime.now()
# z=(x - y).total_seconds()/3600
# print(z)
# exit(0)

totalmisses=42
totalstars=1149
percent=round(totalmisses*100 / (totalstars + totalmisses), 1)

print(percent)