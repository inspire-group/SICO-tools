#!/usr/bin/env python3
# -*- coding: utf-8 -*-
##################################################
# counter_raptor_resilience.py
# compute resilience value for given client and guard sets
# Input:
# List of Tor client ASes (--client_file, default="../data/top400client.txt")
# List of Tor guard ASes (--guard_as_file, default="../data/as_guard.txt")
# CAIDA AS topology (--topology_file, default="../data/20161001.as-rel2.txt")
# Output:
# Tor client to guard resiliences (cg_resilience.json)
##################################################


# clients observe hijacking
# Tor guards get hijacked
# and every AS is a potential adversary
from __future__ import division
import sys
import json
import time
from collections import deque
import math

import argparse
from copy import deepcopy


def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1



weight_i = 0
equal_paths_i = 1
uphill_hops_i = 2
has_peering_i = 3
as_path_length_i = 4
as_path_i = 5

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

def populateAllDictionaries(ans, asRelationshipVal):
    dictionaryOfRelationships[ans] = asRelationshipVal
    addTo(asPathLengthSets, asRelationshipVal[as_path_length_i], asn)
    addTo(uphillHopSets, asRelationshipVal[uphill_hops_i], asn)
    addTo(hasPeeringSets, 1 if asRelationshipVal[has_peering_i] else 0, asn)

# dictionaryOfRelationships is just a list of ASes and their relationship to the client.
# node is an AS.
# dictionaryOfRelationships format: dictionaryOfRelationships[node] = [weight, equal_paths, uphill_hops]
# Understanding relationships: uphill_hops is simply the number of uphil hops on the path between the vantage point and the origin (from the origin's prospective). Minimizing uphill hops is the most important metric in route preference because it represents local preference based on bussiness relationships.
# weight is a hacky solution for counting the AS path length and whether the path as a peering relationship on it at the same time. If no peering relationship, weight is simply the number of downhill hops. If there is a peering relationship, weight is the number of hops plus the total number of ASes so this way the weight of a path with a peering relationship will always be more than that of a path without a peering relationship. This is the second metric for AS path preference.
# equal_paths is not an AS path prefernce metric but rather a method of encoding random path choice into resilience. If two paths tie on the first two metrics, then the number fractional resiliency is the number of equal paths that resolve to the true origin over the number of equal paths that resolve to the adversary plust the number of equal paths that resolve to the true origin.  

# initialize dictionaryOfRelationships
def init(vantagePoint):
    global dictionaryOfRelationships
    dictionaryOfRelationships = {}
    # Graph is deceptively named. It is better throught of as a dictionary of nodes that stores the weight (which seems to do with level of the dictionaryOfRelationships), the equal paths, and the number of uphill hops.
    # This node has no weight, 1 equal path, and 0 uphil hops
    asRelationshipVal = [0, 1, 0, False, 1, vantagePoint]
    populateAllDictionaries(vantagePoint, asRelationshipVal)


# provider to customer
# q_list appears to be a list of ASes to process.
def breath_first_search_provider_customer(listOfASesToProcess):
    global dictionaryOfRelationships, asdict
    # deque does not pop an element, it builts a que out of a list.
    # queOfASesToProcess is the same as listOfASesToProcess but is now in que format.
    queOfASesToProcess = deque(listOfASesToProcess)
    while queOfASesToProcess:
        # gets the current que.
        currentASNBeingProcessed = queOfASesToProcess.popleft()
        # get the current point in the AS dictionaryOfRelationships and store it as currentASNsRelationship
        currentASNsRelationship = dictionaryOfRelationships[currentASNBeingProcessed]

        # asdict is the relationships loaded from the CAIDA file. The format is:
        # asdict[asn] = [[provider-customer edges],[peer-to-peer edges],[customer-provider edges]]
        # asdict[current][0] is the provider-customer edges of the current AS that is being processed.
        for customer in asdict[currentASNBeingProcessed][provider_customer_edges]:
            # every node is a provider customer edge of the current AS.
            if customer not in dictionaryOfRelationships:
                # Increase the weight by 1.
                populateAllDictionaries(customer, [currentASNsRelationship[weight_i] + 1, currentASNsRelationship[equal_paths_i], currentASNsRelationship[uphill_hops_i], currentASNsRelationship[has_peering_i], currentASNsRelationship[as_path_length_i] + 1, customer + " " + currentASNsRelationship[as_path_i]])
                dictionaryOfRelationships[customer] = [currentASNsRelationship[weight_i] + 1, currentASNsRelationship[equal_paths_i], currentASNsRelationship[uphill_hops_i]]
                queOfASesToProcess.append(customer)
            elif dictionaryOfRelationships[customer][weight_i] == currentASNsRelationship[weight_i] + 1 and dictionaryOfRelationships[customer][uphill_hops_i] == currentASNsRelationship[uphill_hops_i]:
                # I think the above line might need to also compare uphill hops not just weights which only take into account downhill hops and peerings.
                # If this customer AS is already in the relationshipDictionary with a weight equal more than the current ASes weight, then simply increase the number of equal paths by the number of equal paths to get to the current AS.
                dictionaryOfRelationships[customer][equal_paths_i] += currentASNsRelationship[equal_paths_i]

# peer to peer
def breath_first_search_peer_peer(listOfASesToProcess):
    global dictionaryOfRelationships, asdict, total_as
    q = deque()
    for asBeingProcessed in listOfASesToProcess:
        for peer in asdict[asBeingProcessed][peer_peer_edges]:
            if peer not in dictionaryOfRelationships:
                # This line might explain weight. Weight for provider to client paths is simply the number of hops (which = downhill hops). If there is peering relationship along the path the weight has a factor of total_as added so the weight of a path with a peering relationship will always be more than a path that is all provider client.
                dictionaryOfRelationships[peer] = [dictionaryOfRelationships[asBeingProcessed][weight_i] + total_as, dictionaryOfRelationships[asBeingProcessed][equal_paths_i], dictionaryOfRelationships[asBeingProcessed][uphill_hops_i]]
                q.append(peer)
            elif dictionaryOfRelationships[peer][weight_i] == dictionaryOfRelationships[asBeingProcessed][weight_i] + total_as and dictionaryOfRelationships[peer][uphill_hops_i] == dictionaryOfRelationships[asBeingProcessed][uphill_hops_i]:
                # almost identical to the line in search provider customer, if the node is already in the relationship dictionary with the expected weight, simpl yincrease the number of equal paths.
                dictionaryOfRelationships[peer][equal_paths_i] += dictionaryOfRelationships[asBeingProcessed][equal_paths_i]
    
    # Every peer edge can be followed by any number of provider customer edges so we simply need to begin processing down the graph after we have inserted a relationship entry for all of the peers we need to process.
    while q:
        currentASNBeingProcessed = q.popleft()
        currentASNsRelationship = dictionaryOfRelationships[currentASNBeingProcessed]

        for customer in asdict[currentASNBeingProcessed][provider_customer_edges]:
            if customer not in dictionaryOfRelationships:
                dictionaryOfRelationships[customer] = [currentASNsRelationship[weight_i] + 1, currentASNsRelationship[equal_paths_i], currentASNsRelationship[uphill_hops_i]]
                q.append(customer)
            elif dictionaryOfRelationships[customer][weight_i] == currentASNsRelationship[weight_i] + 1  and dictionaryOfRelationships[customer][uphill_hops_i] == currentASNsRelationship[uphill_hops_i]:
                dictionaryOfRelationships[customer][equal_paths_i] += currentASNsRelationship[equal_paths_i]

# customer to provider
def breath_first_search_customer_provider(vantagePoint):
    global dictionaryOfRelationships, asdict
    q = deque([vantagePoint])
    curlst = []
    # start at the vantagePoint of the dictionaryOfRelationships. We will then go up to examine this ASes providers.
    curlevel = 0
    while q:
        currentASNBeingProcessed = q.popleft()
        # val is the weight, equal paths, and uphil hops.
        currentASNsRelationship = dictionaryOfRelationships[currentASNBeingProcessed]
        # If we are at a new level, first we search down the graph across peering and customer edges before we continue to look at the provider edges of this new level.
        if currentASNsRelationship[uphill_hops_i] > curlevel:
            # if the value is creater than the current number of uphil hops, go down the dictionaryOfRelationships from each one of the ASes in the current level to populate ASes below in the dictionaryOfRelationships.

            breath_first_search_provider_customer(curlst)

            # now go across to the peers.
            breath_first_search_peer_peer(curlst)

            # reset the list of ASes in the current level.
            curlst = []

            # increase the current level to this ASes level.
            curlevel = currentASNsRelationship[uphill_hops_i]
        for provider in asdict[currentASNBeingProcessed][customer_provider_edges]:
            # node is each AS in the list of providers.
            if provider not in dictionaryOfRelationships:
                # Populate the dictionaryOfRelationships with the values for the new node.
                # node is a provider of the vantagePoint.
                # val[0] is the same because it is the weight. Val 1 is the same because there is only 1 equal length path. val[2] is incremented by 1 such that there is one more uphil hop.
                dictionaryOfRelationships[provider] = [currentASNsRelationship[weight_i], currentASNsRelationship[equal_paths_i], currentASNsRelationship[uphill_hops_i] + 1]
                # put node in the que for processing. next.
                q.append(provider)

                # append node to the list of current nodes in this level.
                curlst.append(provider)
            elif dictionaryOfRelationships[provider][uphill_hops_i] == (currentASNsRelationship[uphill_hops_i]+1):
                # this is the case where we have already fhound a round to this node becuase it was already in the dictionaryOfRelationships.
                # We do not need to compare weights in the above line because the path to provider must either have fewer uphill hops (meaning it was at a previous level) or must have the same number of uphill hops in which case it has not downhill hops because downhill hops at this level have not been populated.
                # thus we increment the number of equal length paths by 1.
                dictionaryOfRelationships[provider][equal_paths_i] += currentASNsRelationship[equal_paths_i]

# traverse nodes to calculate resiliency
def update_resilience(vantagePoint, vantagePointExcluded):
    global dictionaryOfRelationships, originSet, total_as, outFile, currentLineNumber, numberOfVantagePointLines

    if vantagePointExcluded:
        del dictionaryOfRelationships[vantagePoint]
    # sort all the ASes in the dictionaryOfRelationships by 
    # k_v is a dictionaryOfRelationships item.
    # k_v[1] is the value.
    # here we are sorting the ASes by the number of uphil hops primarily and then subsorting by the weight.
    # This is like ORDER BY uphil_hops, weight
    # Here k_v[0] is the ASN, and k_v[1] is the associated data.
    # k_v[1][2] is the number of uphill hops
    # k_v[1][0] is the path weight
    # by generating a tuple, sort is told to sort first by the number of uphill hops and then use the weight as a tie breaker.
    # Sorted uses (primary key, secondary key)
    # I think this could be made more readable with reverse = True and removing the - signs on the key.
    asn_i = 0
    relationship_i = 1
    listOfRelationshipsSortedWithKeys = sorted(list(dictionaryOfRelationships.items()), key=lambda asRelationshipKVP: (-asRelationshipKVP[relationship_i][uphill_hops_i],-asRelationshipKVP[relationship_i][weight_i]))
    # L2 simply turns this from a list of KVPs into a list of AS numbers by dropping all of the associated info.
    listOfASNSSorted = [kvp[asn_i] for kvp in listOfRelationshipsSortedWithKeys]

    # unreachable is the number of ASes that were in the AS dictionaryOfRelationships that we were unable to find a route to from the node.
    # because we could not find a route they are not in the dictionaryOfRelationships and thus not in listOfASNSSorted.
    # so we can subtract the total number of ASes from the ASes in listOfASNSSorted
    # the root that we used to key the dictionaryOfRelationships is not going to be included in listOfASNSSorted but should not be considered an unreachable AS.
    # that is why there is the - 1.
    # The inclusion of the vantage point its self in the result is debateable. If the vantage point is NOT included in listOfASNSSorted it must be removed from this line as well so it is not included as an unreachable AS.
    unreachableASes = None
    if vantagePointExcluded:
        unreachableASes = set(asdict.keys()) - set(listOfASNSSorted) - set([vantagePoint])
    else:
        unreachableASes = set(asdict.keys()) - set(listOfASNSSorted)


    #print "number of unreachable nodes is %i" % unreachable
    # nodes is the number of ASes that have less preferred paths.
    numberOfASesWithLessPreferredPaths = 0
    listOfASesWithLessPreferredPaths = []
    prev = ()
    # This will be used for Beta calculations (num eq paths victim/(num eq paths adversary + num eq paths victim))
    numberOfASesWithEquallyPreferredPaths = 0
    listOfASesWithEquallyPreferredPaths = []

    listOfASesWithMorePreferredPaths = listOfASNSSorted[:]

    firstOrigin = True

    for asn in unreachableASes:
        if asn in originSet:
            resilienceObject = {}
            for attackerASN in unreachableASes:
                if attackerASN != asn:
                    resilienceObject[attackerASN] = 0
            for attackerASN in listOfASesWithMorePreferredPaths:
                resilienceObject[attackerASN] = 0
            if firstOrigin:
                firstOrigin = False
            else:
                outFile.write(",")
            outFile.write('"{}":'.format(asn))
            json.dump(resilienceObject, outFile)


    originsNotInTopology = originSet - set(asdict.keys())

    for asn in originsNotInTopology:
        resilienceObject = {}
        for attackerASN in unreachableASes:
            resilienceObject[attackerASN] = 0
        for attackerASN in listOfASesWithMorePreferredPaths:
            resilienceObject[attackerASN] = 0
        if firstOrigin:
            firstOrigin = False
        else:
            outFile.write(",")
        outFile.write('"{}":'.format(asn))
        json.dump(resilienceObject, outFile)

    if vantagePointExcluded and vantagePoint in originSet:
        resilienceObject = {}
        for attackerASN in unreachableASes:
            resilienceObject[attackerASN] = 1
        for attackerASN in listOfASesWithMorePreferredPaths:
            # This is somewhat misleading but the vantage point is preferable to all ASes.
            resilienceObject[attackerASN] = 1
        if firstOrigin:
            firstOrigin = False
        else:
            outFile.write(",")
        outFile.write('"{}":'.format(vantagePoint))
        json.dump(resilienceObject, outFile)

            
    buffer = []

    resilienceObject = {}
    for attackerASN in unreachableASes:
        resilienceObject[attackerASN] = 1
    for attackerASN in listOfASesWithMorePreferredPaths:
        resilienceObject[attackerASN] = 0
    for asn in listOfASNSSorted:
        print("ASes processed: {}, Percentage: {}".format(total_as - len(listOfASesWithMorePreferredPaths), ((currentLineNumber - 1 + ((total_as - len(listOfASesWithMorePreferredPaths)) / total_as)) / numberOfVantagePointLines) * 100.0))
        currentASNsRelationship = dictionaryOfRelationships[asn]
        if prev==(currentASNsRelationship[weight_i],currentASNsRelationship[uphill_hops_i]):
            numberOfASesWithEquallyPreferredPaths += 1
            listOfASesWithEquallyPreferredPaths.append((asn, currentASNsRelationship[equal_paths_i]))
            if asn in originSet:
                buffer.append((asn,currentASNsRelationship[equal_paths_i]))
            listOfASesWithMorePreferredPaths.remove(asn)
        else:
            for asnEqualPathsTuple in buffer:

                # this line puts the resiliance of each tor node in from the perspective of the client we constructed the dictionaryOfRelationships for.
                # It computes the number of ASes that can NOT hijack this tor node.
                # It is a number of ASes not a percentage. It is normalized to a percentage around line 267 where it is divided by the toal ASes - 2
                # I think this line might be wrong as well because we need to add the number of equal paths that this ASN has / this ASNs equal paths + each competitors equal paths at this level. Not just a single addition.
                # The current caluclation the equal paths portion of the resilience cannot count more than a single ASN, but if an ASN is equal with 4 ASNs and has 1 equal path, it should have a resilience of 2 ANS (before deviding by total ASNs) or .5 after dividing.
                # We need to subtract .5 from the summation of Beta to prevent double counting an ASes path to its self in beta.
                
                # compute the resiliences for ASes with equally preferred paths
                # Less and more preferrred paths should already be in the resilience object.
                for attackerASNEqualPathsTuple in listOfASesWithEquallyPreferredPaths:
                    if attackerASNEqualPathsTuple[0] != asnEqualPathsTuple[0]:
                        resilienceObject[attackerASNEqualPathsTuple[0]] = asnEqualPathsTuple[1] / (asnEqualPathsTuple[1] + attackerASNEqualPathsTuple[1])
                    else:
                        del resilienceObject[asnEqualPathsTuple[0]]
                if firstOrigin:
                    firstOrigin = False
                else:
                    outFile.write(",")
                outFile.write('"{}":'.format(asnEqualPathsTuple[0]))
                json.dump(resilienceObject, outFile)
                # Flushing output allows for better crash recovery but slows down performance.
                #outFile.flush()
            

            numberOfASesWithLessPreferredPaths += numberOfASesWithEquallyPreferredPaths
            listOfASesWithLessPreferredPaths.extend([asnTuple[0] for asnTuple in listOfASesWithEquallyPreferredPaths])

            for attackerASNEqualPathsTuple in listOfASesWithEquallyPreferredPaths:
                resilienceObject[attackerASNEqualPathsTuple[0]] = 1

            numberOfASesWithEquallyPreferredPaths = 1
            listOfASesWithEquallyPreferredPaths = [(asn,currentASNsRelationship[equal_paths_i])]
            prev = (currentASNsRelationship[weight_i],currentASNsRelationship[uphill_hops_i])
            if asn in originSet:
                buffer = [(asn,currentASNsRelationship[equal_paths_i])]
            else:
                buffer = []
            listOfASesWithMorePreferredPaths.remove(asn)
    # leftover ASes in buffer
    for asnEqualPathsTuple in buffer:
        if firstOrigin:
            firstOrigin = False
        else:
            outFile.write(",")
        for attackerASNEqualPathsTuple in listOfASesWithEquallyPreferredPaths:
            if attackerASNEqualPathsTuple[0] != asnEqualPathsTuple[0]:
                resilienceObject[attackerASNEqualPathsTuple[0]] = asnEqualPathsTuple[1] / (asnEqualPathsTuple[1] + attackerASNEqualPathsTuple[1])
            else:
                del resilienceObject[asnEqualPathsTuple[0]]
        outFile.write('"{}":'.format(asnEqualPathsTuple[0]))
        json.dump(resilienceObject, outFile)
        #outFile.flush()
def parse_args():
    parser = argparse.ArgumentParser()
    # This is a CAIDA AS topology.
    parser.add_argument("--topology_file",
                        default="./20190301.as-rel2.txt")
    # These are the ASes that we are using as vantage points.
    parser.add_argument("--client_file",
                        default="../data/vantage-points.txt")
    # These are the ASNs that we are calculating the resilience for.
    parser.add_argument("--guard_as_file",
                        default="../data/origins.txt")
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


    with open("./list of ASNs with full community support.txt") as fullSupportFile:
        for line in fullSupportFile:
            asnsWithFullCommunitySupport.add(line.strip())

    with open("./as_forward.csv") as forwardFile:
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

