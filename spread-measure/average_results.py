import sys

synResults = sys.argv[1]
pingResults = sys.argv[2]


synVictimPercentage = 0
pingVictimPercentage = 0

victimPercentagePrefix = "Victim percentage: "

for rline in open(synResults):
  line = rline.strip()
  if line.startswith(victimPercentagePrefix):
    synVictimPercentage = float(line.replace(victimPercentagePrefix, ""))

for rline in open(pingResults):
  line = rline.strip()
  if line.startswith(victimPercentagePrefix):
    pingVictimPercentage = float(line.replace(victimPercentagePrefix, ""))



avgVictimPercentage = float(synVictimPercentage + pingVictimPercentage) / 2.0
print("Average victim percentage: {}".format(avgVictimPercentage))
print("Average adversary percentage: {}".format(100 - avgVictimPercentage))