import sys


victimResponses = set([])

adversaryResponses = set([])



for line in open(sys.argv[1]):
  victimResponses.add(line)

for line in open(sys.argv[2]):
  adversaryResponses.add(line)


overlap = victimResponses.intersection(adversaryResponses)
overlapCount = len(overlap)

# Do not count hosts that sent to both the victim and the adversary for either the adversary or the victim.
adversaryUniqueCount = len(adversaryResponses) - overlapCount

victimUniqueCount = len(victimResponses) - overlapCount

print("Total responders: {}".format(adversaryUniqueCount + victimUniqueCount + overlapCount))

print("Overlap count: {}".format(overlapCount))

print("Sample size: {}".format(victimUniqueCount + adversaryUniqueCount))

print("Victim percentage: {}".format(100.0 * float(victimUniqueCount) / float(victimUniqueCount + adversaryUniqueCount)))

print("Adversary percentage: {}".format(100.0 * float(adversaryUniqueCount) / float(victimUniqueCount + adversaryUniqueCount)))