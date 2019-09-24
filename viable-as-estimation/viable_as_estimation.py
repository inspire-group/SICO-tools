#!/usr/bin/env python3
# -*- coding: utf-8 -*-
##################################################
# viable-as_estimation.py
##################################################

# in case someone uses python 2.
from __future__ import division
import sys
import json
import time
from collections import deque
import math

import argparse
from copy import deepcopy




provider_customer_edges = 0
peer_peer_edges = 1
customer_provider_edges = 2


asPathLengthSets = {}
uphillHopSets = {}
hasPeeringSets = {}

def addTo(dictionary, index, asn):
    if index in dictionary:
        dictionary[index].add(asn)
    else:
        dictionary[index] = set([asn])





def parse_args():
    parser = argparse.ArgumentParser()
    # This is a CAIDA AS topology.
    parser.add_argument("--topology_file",
                        default="./20190301.as-rel2.txt")
    parser.add_argument("--as_forward",
                        default= "./as_forward.csv")
    parser.add_argument("--as_full_support",
                        default= "./as_full_support.csv")
    return parser.parse_args()

outFile = None

currentLineNumber = 0
numberOfVantagePointLines = 0


def isTier1(asn):
    if asdict[asn][customer_provider_edges] != []:
        return False
    return countAllDownstreams(asn) > .8 * len(asdict)

def isStub(asn):
    global asdict, originSet, dictionaryOfRelationships, total_as, outFile, currentLineNumber, numberOfVantagePointLines
    return len(asdict[asn][provider_customer_edges]) == 0

def hasNoPeers(asn):
    global asdict, originSet, dictionaryOfRelationships, total_as, outFile, currentLineNumber, numberOfVantagePointLines
    return len(asdict[asn][peer_peer_edges]) == 0


def countAllDownstreams(asn):
    return len(set.union(setPeersAndDowstreamsOfPears(asn), clientSet(asn)))

asnCount = 0
def countPeersAndDownstreamsOfPeers(asn):
    global asnCount
    asnCount += 1
    print("%d ASNs computed.", asnCount)
    return len(setPeersAndDowstreamsOfPears(asn))

def setPeersAndDowstreamsOfPears(asn):
    global asnCount, asdict, originSet, dictionaryOfRelationships, total_as, outFile, currentLineNumber, numberOfVantagePointLines
    downstreamSet = set([])
    for peer in asdict[asn][peer_peer_edges]:
        downstreamSet.add(peer)
        downstreamSet.update(clientSet(peer))
    return downstreamSet

clientSetDict = {}
def clientSet(asn):
    global clientSetDict, asdict, originSet, dictionaryOfRelationships, total_as, outFile, currentLineNumber, numberOfVantagePointLines
    if asn in clientSetDict:
        return clientSetDict[asn]
    asdictRes = asdict[asn]
    if len(asdictRes[provider_customer_edges]) == 0:
        return set([])
    else:
        clientSetRes = set.union(set(asdictRes[provider_customer_edges]), *[clientSet(customer) for customer in asdictRes[provider_customer_edges]])
        clientSetDict[asn] = clientSetRes
        return clientSetRes

def providersPeer(asn):
    providerSet = set(asdict[asn][customer_provider_edges])
    providerPeeringSet = set([])
    for provider in providerSet:
        peerSet = set(asdict[provider][peer_peer_edges])
        peerSet.add(provider)
        # See if this provider is peering with all the other providers.
        if providerSet.issubset(peerSet):
            providerPeeringSet.add(provider)
    return providerSet == providerPeeringSet

def anyProvidersPeer(asn):
    providerSet = set(asdict[asn][customer_provider_edges])
    for provider in providerSet:
        for providerPeer in asdict[provider][peer_peer_edges]:
            if providerPeer in providerSet:
                return True
    return False

def noProviderIsTier1(asn, tier1s):
    for provider in asdict[asn][customer_provider_edges]:
        if provider in tier1s:
            return False
    return True
tpologyDepthDict = {}
def topologyDepth(asn, tier1s):
    global tpologyDepthDict

    if asn in tier1s:
        return 1

    if asn in tpologyDepthDict:
        return tpologyDepthDict[asn]
    
    providerList = asdict[asn][customer_provider_edges]
    if providerList == []:
        tpologyDepthDict[asn] = sys.maxsize / 2
        return sys.maxsize / 2

    res = min([topologyDepth(provider, tier1s) for provider in providerList]) + 1
    tpologyDepthDict[asn] = res
    return res

asnsWithFullCommunitySupport = set()
def hasProviderWithFullSupport(asn):
    asdictRes = asdict[asn]
    providers = asdictRes[customer_provider_edges]
    for provider in providers:
        if provider in asnsWithFullCommunitySupport:
            return True
    return False

asesThatForwardCommunities = set()
def hasProviderThatForwardsCommunities(asn):
    asdictRes = asdict[asn]
    providers = asdictRes[customer_provider_edges]
    for provider in providers:
        if provider in asesThatForwardCommunities:
            return True
    return False

def hasForwardingPathToFullCommunitySupport(asn, tierN, tier1s):
    # tier1s is unused. Simply left as a parameter for flexibility in case it should be used in a calculation.
    asdictRes = asdict[asn]
    providers = asdictRes[customer_provider_edges]
    # See if one of the immediat providers supports communities.
    for provider in providers:
        if provider in asnsWithFullCommunitySupport:
            return True

    # Just the list of providers as a set
    providerSet = set(providers)
    # If not, see if its providers forward communities
    for provider in providers:
        if provider in asesThatForwardCommunities:
            

            # See if this provider peers with all other providers (only need to be evaluated on first level above customer) which means that forwarding communities is not enough.
            if tierN:
                provicerPeerSet = set(asdict[provider][peer_peer_edges])
                provicerPeerSet.add(provider)
                # See if this provider is peering with all the other providers. If so, it is bad news for this route because the annoucment cannot be suppressed to the other providers.
                if providerSet.issubset(provicerPeerSet):
                    continue

            # If a provider forwards communities, does one of its providers support communities or forward to another provider that does?
            if hasForwardingPathToFullCommunitySupport(provider, False, tier1s):
                return True
    return False

def main(args):
    global asdict, originSet, dictionaryOfRelationships, total_as, outFile, currentLineNumber, numberOfVantagePointLines
    asdict = {}
    peerLinkCount = 0
    # load AS relationships from CAIDA topo file
    # every [provider-customer edgees] is a list of ASes that are customers.
    # This should really be thoruhg of as:
    # asdict[asn] = [[customer ASNs],[peers],[providers]]
    # asdict[asn] = [[provider-customer edges],[peer-to-peer edges],[customer-provider edges]]
    for line in open(args.topology_file):
        # line here is a line of the file.
        if not line.strip().startswith("#"):
            # arr is the line of the topology file split.
            arr = line.strip().split('|')

            asn1 = arr[0]
            asn2 = arr[1]

            rel = int(arr[2]) # -1: provider-customer; 0: peer-to-peer
            if rel == 0:
                peerLinkCount += 1

            if asn1 in asdict:
                asdict[asn1][rel+1].append(asn2)
            else:
                asdict[asn1] = [[],[],[]]
                asdict[asn1][rel+1] = [asn2]
            if asn2 in asdict:
                # This is confusing but it is simply adding as1 to the peer to peer list if its relationship was peer to peer or the provider list if it is a provider.
                asdict[asn2][abs(rel)+1].append(asn1)
            else:
                asdict[asn2] = [[],[],[]]
                asdict[asn2][abs(rel)+1] = [asn1]


    with open(args.as_full_support) as fullSupportFile:
        for line in fullSupportFile:
            asnsWithFullCommunitySupport.add(line.strip())

    with open(args.as_forward) as forwardFile:
        for line in forwardFile:
            line = line.strip()
            if line == "":
                continue
            asesThatForwardCommunities.add(line)
    # originSet will eventually become the resiliance of every origin node.
    total_as = len(asdict)
    print("%d ASes found in topology", total_as)
    print("%d peering links", peerLinkCount)
    print("%d stub ASes", len([1 for asn in asdict.keys() if isStub(asn)]))
    print("%d ASes with no peers", len([1 for asn in asdict.keys() if hasNoPeers(asn)]))
    print("%d super lonely", len([1 for asn in asdict.keys() if hasNoPeers(asn) and isStub(asn)]))

    tier1s = [asn for asn in asdict.keys() if isTier1(asn)]
    print("%d tier 1s", tier1s)

    customersOfTier1s = [len(clientSet(asn)) for asn in tier1s]
    print("%d tier1 customers", [(tier1s[i], customersOfTier1s[i]) for i in range(len(tier1s))])
    print("%d average customers of tier1s", float(sum(customersOfTier1s)) / len(customersOfTier1s))
    print("%d median customers of tier1s", customersOfTier1s[int(len(customersOfTier1s) / 2)])
    #print("2914 downstreams: %d", countAllDownstreams("2914"))
    #print("2914 tier1?", isTier1("2914"))


    multiHomed = [asn for asn in asdict.keys() if len(asdict[asn][customer_provider_edges]) >= 2]
    print("%d multi homed ASes", len(multiHomed))

    multiHomedStubs = [asn for asn in multiHomed if isStub(asn)]
    print("%d multi homed stub ASes", len(multiHomedStubs))

    print("%d multi homed ASes with a provider with full commuinty support", len([asn for asn in multiHomed if hasProviderWithFullSupport(asn)]))
    print("%d multi homed ASes with a provider that forwards communities", len([asn for asn in multiHomed if hasProviderThatForwardsCommunities(asn)]))
    print("%d multi homed ASes with a provider that forwards communities or has full community support", len([asn for asn in multiHomed if hasProviderThatForwardsCommunities(asn) or hasProviderWithFullSupport(asn)]))
    print("%d multi homed ASes with a forwarding path to full community support", len([asn for asn in multiHomed if hasForwardingPathToFullCommunitySupport(asn, True, tier1s)]))


    topologyDepthsSorted = sorted([td for td in [topologyDepth(asn, tier1s) for asn in multiHomed] if td < sys.maxsize / 2])
    print("%d average topology depth", float(sum(topologyDepthsSorted)) / len(topologyDepthsSorted))
    print("%d topology depth greater than 3 count", float(len([1 for td in topologyDepthsSorted if td > 3])))




    multiHomedWithoutTier1 = [asn for asn in multiHomed if noProviderIsTier1(asn, tier1s)]
    print("%d multi homed ASes without any tier 1 providers", len(multiHomedWithoutTier1))

    numberOfProvidersForMultihomedWithoutTier1 = sorted([len(asdict[asn][customer_provider_edges]) for asn in multiHomedWithoutTier1])
    print("%d avg number of providers for multihomed that does not have tier1", float(sum(numberOfProvidersForMultihomedWithoutTier1)) / len(numberOfProvidersForMultihomedWithoutTier1))
    multiHomedWithoutTier1ProbabilitiesForwardCommunitiesSorted = sorted([1 - (math.pow(.86, len(asdict[asn][customer_provider_edges]))) for asn in multiHomedWithoutTier1])
    print("%d avg probability that a single provider will forward communities for a multi homed AS", float(sum(multiHomedWithoutTier1ProbabilitiesForwardCommunitiesSorted)) / len(multiHomedWithoutTier1ProbabilitiesForwardCommunitiesSorted))
    print("%d min probability", multiHomedWithoutTier1ProbabilitiesForwardCommunitiesSorted[0])
    print("%d median probability that a single provider will forward communities for a multi homed AS", multiHomedWithoutTier1ProbabilitiesForwardCommunitiesSorted[int(len(multiHomedWithoutTier1ProbabilitiesForwardCommunitiesSorted) / 2)])



    multiHomedWithoutTier1ProvidersPeer = [asn for asn in multiHomedWithoutTier1 if anyProvidersPeer(asn)]
    print("%d multi homed non-tier-1 any providers peer", len(multiHomedWithoutTier1ProvidersPeer))

    multiHomedWithoutTier1AllProvidersPeer = [asn for asn in multiHomedWithoutTier1 if providersPeer(asn)]
    print("%d multi homed non-tier-1 all providers peer", len(multiHomedWithoutTier1AllProvidersPeer))


    print("%d multi homed two providers", len([1 for asn in multiHomed if len(asdict[asn][customer_provider_edges]) == 2]))
    countMultiHomedProvidersPeer = len([1 for asn in multiHomed if providersPeer(asn)])
    print("%d multi homed providers peer", countMultiHomedProvidersPeer)



    print("%d avg peering edges", float(sum([len(rels[peer_peer_edges]) for rels in asdict.values()])) / total_as)
    peeringEdgeCountList = [len(rels[peer_peer_edges]) for rels in asdict.values()]
    peeringEdgeCountListSorted = sorted(peeringEdgeCountList)
    print("%d median peering edges", peeringEdgeCountListSorted[int(len(peeringEdgeCountListSorted) / 2)])
    upstreamProviderCountList = [len(rels[customer_provider_edges]) for rels in asdict.values()]
    upstreamProviderCountListSorted = sorted(upstreamProviderCountList)
    print("%d median upstream providers", upstreamProviderCountListSorted[int(len(upstreamProviderCountListSorted) / 2)])
    print("%d avg peering edges that have downstreams", float(sum(
        [
        len([1 for peer in rels[peer_peer_edges] if not isStub(peer)])
         for rels in asdict.values()])) 
    / total_as)

    notStubs = [asn for asn in asdict if not isStub(asn)]
    downstreams = [len(clientSet(asn)) for asn in notStubs]
    print("%d avg downstreams of providers", float(sum(downstreams)) / len(downstreams))
    # note that the output is keyed by client.
    # it is a 2d map. The first level is the client ASN. Within the client AS we have a map
    #asesNotLonely = [asn for asn in asdict if not (hasNoPeers(asn) and isStub(asn))]
    #asesReachableSorted = sorted([countAllDownstreams(asn) for asn in asesNotLonely])
    #print("%d median ASes reachable by not lonely ASes", asesReachableSorted[int(len(asesReachableSorted) / 2)])
    #print("%d average ASes reachable by not lonely ASes", float(sum(asesReachableSorted)) / len(asesReachableSorted))
    #print("%d max ASes reachable vie non-provider routes", nonProviderRoutesSorted[len(nonProviderRoutesSorted) - 1])
    #print("%d ", countAllDownstreams("53698"))
if __name__ == '__main__':
    main(parse_args())

