# encoding=utf-8
import time
t_start = time.time()

import re
import json
import math

from util import load_standard_address, build_reversed_index
from filter_address_noise import remove_address_noise

ADDRESS_LIB = None
REVERSED_INDEX = None
STANDARD_ADDRESS_LIB_PATH = 'data/address_library_all.csv'
DEBUG = True


def standard_match(addressTxt, candidateStdAddress):

    idSSCandts = map(lambda x: (x[0], x[1]['street']+x[1]['street_num']),
                     enumerate(candidateStdAddress))
    matchedIdSSCandts = list(filter(
        lambda x: x[1] == addressTxt and len(x[1]), idSSCandts))
    if len(matchedIdSSCandts) == 0:
        return None  # street+street_num not in txt
    if len(matchedIdSSCandts) == 1:
        return candidateStdAddress[matchedIdSSCandts[0][0]]
    maxLen = max(map(lambda x: len(x[1]), matchedIdSSCandts))
    maxLenIdSSCandts = list(filter(lambda x: maxLen == len(x[1]),
                                   matchedIdSSCandts))
    if len(maxLenIdSSCandts) == 1:
        return candidateStdAddress[maxLenIdSSCandts[0][0]]
    idOtherAddressTxts = map(lambda m: (m[0], addressTxt.replace(m[1], '')),
                             maxLenIdSSCandts)
    idOtherAddressTxts = list(filter(lambda x: len(x[1]), idOtherAddressTxts))
    if len(idOtherAddressTxts) == 0:
        # multiple max length street+street_num in txt
        return list(map(lambda i: candidateStdAddress[i[0]],
                        maxLenIdSSCandts))
    # TODO: check order of match field.
    priorityMatchField = ['township', 'district', 'city', 'province']
    return match_addition_field(priorityMatchField, idOtherAddressTxts,
                                candidateStdAddress)


def match_addition_field(fields, idAddressTxts, candidateStdAddress):
    matchedStdAddress = list(map(lambda x: candidateStdAddress[x[0]],
                                 idAddressTxts))
    for idx, field in enumerate(fields):
        # TODO: postfix(city, province, township et al.)
        subCandidates = list(filter(
            lambda x: candidateStdAddress[x[0]][field] in x[1],
            idAddressTxts))
        if len(subCandidates) == 0:
            return matchedStdAddress
        if len(subCandidates) == 1:
            return candidateStdAddress[subCandidates[0][0]]
        idAddressTxts = map(lambda x: (x[0], x[1].replace(
            candidateStdAddress[x[0]][field], '')), subCandidates)
        idAddressTxts = list(filter(lambda x: len(x[1]), idAddressTxts))
        if len(idAddressTxts) == 0:
            return list(map(lambda x: candidateStdAddress[x[0]], subCandidates))
        matchedStdAddress = list(map(lambda x: candidateStdAddress[x[0]],
                                     idAddressTxts))
    return matchedStdAddress


def filter_nearby_streetNum(streetNumTxt, streetNums):
    """
        return:
           list, matched item idx
           list, upNeighbors
           list, downNeighbors
           list, upBounds
           list, downBounds
    """
    streetNumTxtValues = list(filter(len, re.split(r'[^\d]', streetNumTxt)))
    if not len(streetNumTxtValues):
        matchedIdxs, _ = filter_nearby_street_NonNum(streetNumTxt, streetNums)
        return matchedIdxs, [], [], [], []

    idxStreetNumValues = list(map(
        lambda sn: (sn[0], list(filter(len, re.split(r'[^\d]', sn[1])))),
        enumerate(streetNums)))
    idxStreetNumValuesTMP = list(filter(
        lambda x: len(x[1]) > 0, idxStreetNumValues))
    sameNumValues = list(filter(lambda x: x[1] == streetNumTxtValues,
                                idxStreetNumValuesTMP))
    if len(sameNumValues):
        matchedIdxs = list(map(lambda x: x[0], sameNumValues))
        return matchedIdxs, [], [], [], []

    assert len(idxStreetNumValuesTMP) > 1, '{} {}'.format(streetNumTxt, streetNums)
    streetNumFlag = int(streetNumTxtValues[0]) % 2
    idxStreetNumValuesTMP = list(filter(
        lambda x: int(x[1][0]) % 2 == streetNumFlag,
        idxStreetNumValuesTMP))
    if len(idxStreetNumValuesTMP) <= 3:
        # TODO: not same flag street_num.
        idxStreetNumValuesTMP = list(filter(lambda x: len(x[1]), idxStreetNumValues))
    # 3#  --> 3#1 3#4
    # 3#1#2  --> 3#1 3#1#7
    # 3#1#2  --> 3#1 3#1
    # 3#1#2 --> 1#
    # 3#3 --> 3#2 3#4
    # 3# --> 5# 1#
    for idx, num in enumerate(streetNumTxtValues):
        tmp = list(filter(lambda x: len(x[1]) > idx and x[1][idx] == num,
                          idxStreetNumValuesTMP))
        if not tmp:
            break
        idxStreetNumValuesTMP = tmp
    if len(idxStreetNumValuesTMP) == 1:
        matchedIdxs = [idxStreetNumValuesTMP[0][0]]
        return matchedIdxs, [], [], [], []

    minLen = min(map(lambda x: len(x[1]), idxStreetNumValuesTMP))
    if minLen > len(streetNumTxtValues):
        idxStreetNumValuesTMP = sorted(idxStreetNumValuesTMP, key=lambda x: x[1][idx+1])
        matchedIdxs = [idxStreetNumValuesTMP[0][0]]
        # 3# --> 3#1 > 3#9
        return matchedIdxs, [], [], [], []
    # get neighbors with nearest street_num,like [22, 26] for 24.
    indicator = max(minLen-1, idx)
    tmp = 2 if indicator == 0 else 1
    neighborNums = [int(num)+tmp, int(num)-tmp]
    upNeighbors, downNeighbors, parents = list(), list(), list()
    for idxTMP, numTMP in idxStreetNumValuesTMP:
        if len(numTMP) > indicator and int(numTMP[idx]) not in neighborNums:
            continue
        if len(numTMP) <= indicator:
            parents.append(idxTMP)
            continue
        beUpNeighbor = (neighborNums[0] == int(numTMP[idx]))
        if beUpNeighbor:
            upNeighbors.append(idxTMP)
        else:
            downNeighbors.append(idxTMP)
    if len(upNeighbors) + len(downNeighbors) == 1:
        matchedIdxs = upNeighbors + downNeighbors
        return matchedIdxs, [], [], [], []
    if upNeighbors and downNeighbors:
        # 3#3 --> 3#2 3#4
        # 1# --> 3# 5#
        return [], upNeighbors, downNeighbors, [], []

    idxStreetNumValuesTMP = list(filter(lambda x: len(x[1]) > indicator,
                                        idxStreetNumValuesTMP))
    if not idxStreetNumValuesTMP:
        matchedIdxs = parents
        # 3#3 --> 3#
        return matchedIdxs, [], [], [], []
    # 3#3 --> [3#] 3#5 3#1
    # 3#
    upBounds, downBounds = list(), list()
    tmp = list(filter(lambda x: len(x[1]) <= indicator, idxStreetNumValuesTMP))
    matchedIdxs = list(map(lambda x: x[0], tmp))
    diffs = list(map(lambda x: (x[0], int(x[1][1][indicator]) - int(num)),
                     enumerate(idxStreetNumValuesTMP)))
    upDiffs = list(filter(lambda x: x[1] > 0, diffs))
    downDiffs = list(filter(lambda x: x[1] < 0, diffs))
    upValue = min(upDiffs, key=lambda x: x[1])[1] if upDiffs else 10000
    downValue = max(downDiffs, key=lambda x: x[1])[1] if downDiffs else -10000
    for i, diff in diffs:
        if diff not in [upValue, downValue]:
            continue
        if not upNeighbors and diff == upValue:
            upBounds.append(idxStreetNumValuesTMP[i][0])
        if not downNeighbors and diff == downValue:
            downBounds.append(idxStreetNumValuesTMP[i][0])
    return [], upNeighbors, downNeighbors, upBounds, downBounds


def post_choose_possible_address(stdAddresses):

    numIndexs = get_same_street_item(stdAddresses[0])
    # assert len(numIndexs) >= len(stdAddresses), '{}'.format(stdAddresses)
    otherNumIndexs = list(filter(lambda i: ADDRESS_LIB[i] not in stdAddresses,
                                 numIndexs))
    if len(otherNumIndexs) == 0:
        return [stdAddresses[0]]

    minDisCandts = []
    for index, stdAddress in enumerate(stdAddresses):
        X, Y = (float(stdAddress['locationx']), float(stdAddress['locationy']))
        distances = map(
            lambda i: ((float(ADDRESS_LIB[i]['locationx']) - X)*10**4) ** 2 +
                      ((float(ADDRESS_LIB[i]['locationy']) - Y)*10**4) ** 2,
            otherNumIndexs)
        minDisCandts.append((stdAddresses[index], min(distances)))
    matchedItem = sorted(minDisCandts, key=lambda x: x[1])[0][0]
    return [matchedItem]


def post_calculate_nearby_address(
        streetNumTxt, upNeighbors, downNeighbors, upBounds, downBounds,
        candtsStdAddrs):

    def unique_point(points, candts):
        point = min(map(
            lambda x: (x, sum(map(
                lambda y: distance(candtsStdAddrs[x], candtsStdAddrs[y]),
                candts))),
            points),
            key=lambda x: x[1])
        return [point[0]]
    downs = downNeighbors if downNeighbors else downBounds
    ups = upNeighbors if upNeighbors else upBounds
    # TODO: check more reasonable
    if not downs:
        upCandts = upNeighbors if upNeighbors else upBounds
        index = sorted(upCandts, key=lambda x: candtsStdAddrs[x]['street_num'])[0]
        return [candtsStdAddrs[index]]
    if not ups:
        downCandts = downNeighbors if downNeighbors else downBounds
        index = sorted(downCandts, key=lambda x: candtsStdAddrs[x]['street_num'])[0]
        return [candtsStdAddrs[index]]

    if len(upNeighbors) > 1:
        upNeighbors = unique_point(upNeighbors, downs)
    if len(downNeighbors) > 1:
        downNeighbors = unique_point(downNeighbors, ups)
    if len(upBounds) > 1:
        upBounds = unique_point(upBounds, downs)
    if len(downBounds) > 1:
        downBounds = unique_point(downBounds, ups)

    if upNeighbors and not downNeighbors:
        return [candtsStdAddrs[upNeighbors[0]]]
    if downNeighbors and not upNeighbors:
        return [candtsStdAddrs[downNeighbors[0]]]
    if upNeighbors and downNeighbors:
        address = calculate_location_with_neighbor(
            upNeighbors[0], downNeighbors[0], candtsStdAddrs)
        address.update({'street_num': streetNumTxt})
        candtsStdAddrs[0].update(address)
        return [candtsStdAddrs[0]]
    if upBounds and not downBounds:
        return [candtsStdAddrs[upBounds[0]]]
    if downBounds and not upBounds:
        return [candtsStdAddrs[downBounds[0]]]
    assert upBounds and downBounds
    address = calculate_location_with_bound(
        streetNumTxt, upBounds[0], downBounds[0], candtsStdAddrs)
    address.update({'street_num': streetNumTxt})
    candtsStdAddrs[0].update(address)
    return [candtsStdAddrs[0]]


def calculate_location_with_neighbor(point0, point1, candtsStdAddrs):
    x0, y0 = (float(candtsStdAddrs[point0]['locationx']),
              float(candtsStdAddrs[point0]['locationy']))
    x1, y1 = (float(candtsStdAddrs[point1]['locationx']),
              float(candtsStdAddrs[point1]['locationy']))
    x, y = (x0 + x1) / 2, (y0 + y1) / 2
    return {'locationx': str(x), 'locationy': str(y)}


def calculate_location_with_bound(numTxt, point0, point1,
                                  candtsStdAddrs):
    txts = [numTxt, candtsStdAddrs[point0]['street_num'],
            candtsStdAddrs[point1]['street_num']]
    v, v0, v1 = list(map(
        lambda txt: list(map(float, filter(len, re.split(r'[^\d]', txt)))),
        txts))
    x0, y0 = (float(candtsStdAddrs[point0]['locationx']),
              float(candtsStdAddrs[point0]['locationy']))
    x1, y1 = (float(candtsStdAddrs[point1]['locationx']),
              float(candtsStdAddrs[point1]['locationy']))
    x, y = linear_interpolation_location(v, v0, v1, [x0, y0], [x1, y1])
    return {'locationx': str(x), 'locationy': str(y)}


def linear_interpolation_location(n, n0, n1, loc0, loc1):
    indicator = 0
    minLen = min(map(len, [n, n0, n1]))
    while (minLen > indicator and (
            n[indicator] == n0[indicator] == n1[indicator])):
        indicator += 1
    if minLen <= indicator:
        indicator = minLen - 1
    ratio = abs(n[indicator]-n0[indicator])/abs(n1[indicator]-n0[indicator])
    x = loc0[0] + (loc1[0] - loc0[0]) * ratio
    y = loc0[1] + (loc1[1] - loc0[1]) * ratio
    return x, y


def get_same_street_item(item):
    feildNames = ['province', 'city', 'district', 'township', 'street']
    filterFeildValues = list(map(lambda x: (x, item[x]), feildNames))
    numIndexs = set()
    for field, value in filterFeildValues:
        if not value:
            continue
        fieldSet = REVERSED_INDEX[field][value]
        if not numIndexs:
            numIndexs = fieldSet
            continue
        numIndexs = numIndexs.intersection(fieldSet)
    return numIndexs


def distance(item0, item1):
    idx0X, idx0Y = (float(item0['locationx']),
                    float(item0['locationy']))
    idx1X, idx1Y = (float(item1['locationx']),
                    float(item1['locationy']))
    tmpDis = ((idx0X - idx1X)*10**4) ** 2 + ((idx0Y - idx1Y)*10**4) ** 2
    return tmpDis


def filter_nearby_street_NonNum(addressTxt, streetNonNums):
    matchedIdx, minDistance = list(), 10**6
    for idx, streetTxt in enumerate(streetNonNums):
        dis = - len(set(streetTxt) & set(addressTxt))
        if dis < minDistance:
            minDistance = dis
            matchedIdx = [idx]
        elif dis == minDistance:
            matchedIdx.append(idx)
        else:
            continue
    return matchedIdx, list(map(lambda x: streetNonNums[x], matchedIdx))


def match_approximate_address(addressTxt, candidateStdAddress, topn=1):
    if topn >= len(candidateStdAddress):
        return candidateStdAddress
    streetNumCandts = list(map(lambda x: x['street_num'],
                               candidateStdAddress))
    STREET_NUM_EXPR = r'[\d\-之附a-z#]+[号栋座店#]?[\d]*'
    streetNumTxt = addressTxt['street_num']
    notHasNum = re.search(STREET_NUM_EXPR, streetNumTxt) is None
    matchedIdxs, upNeighbors, downNeighbors, upBounds, downBounds = (
        [] for _ in range(5))
    if notHasNum:
        matchedIdxs, _ = filter_nearby_street_NonNum(streetNumTxt,
                                                     streetNumCandts)
    else:
        tmps = filter_nearby_streetNum(streetNumTxt, streetNumCandts)
        matchedIdxs, upNeighbors, downNeighbors, upBounds, downBounds = tmps

    if len(matchedIdxs) > 1:
        matchedItems = post_choose_possible_address(list(map(
            lambda x: candidateStdAddress[x], matchedIdxs)))
    elif not matchedIdxs:
        matchedItems = post_calculate_nearby_address(
            streetNumTxt, upNeighbors, downNeighbors, upBounds, downBounds,
            candidateStdAddress)
    else:
        matchedItems = [candidateStdAddress[matchedIdxs[0]]]
    return matchedItems


def search_candidate_stdAddress(addresses, fieldUnion=False):
    global REVERSED_INDEX
    candidateStdAdresses = dict()
    # TODO: check negative impact for ignore street_num.
    # ! default order may not be obey by sample.
    priorityFields = ['street', 'township', 'district', 'city', 'province']
    for index, address in addresses.items():
        candidates = set()
        for field in priorityFields:
            fieldRelatedIndex = REVERSED_INDEX[field]
            fieldValue = address.get(field, None)
            if not fieldValue:
                continue
            fieldCandidates = fieldRelatedIndex[fieldValue]
            if fieldUnion:
                candidatesTMP = candidates.union(fieldCandidates)
            else:
                candidatesTMP = candidates.intersection(fieldCandidates) if len(
                    candidates) else fieldCandidates
            if not candidatesTMP:
                continue
            candidates = candidatesTMP
        candidateStdAdresses[index] = candidates
    return candidateStdAdresses


def match(extractedAddressPath, outputPath):
    addressTxts = remove_address_noise(extractedAddressPath,
                                       stdAddressLib=ADDRESS_LIB,
                                       reversedIndex=REVERSED_INDEX,
                                       debug=DEBUG)
    print('search candidates ...')
    candidateStdAddressIndexs = search_candidate_stdAddress(
        addressTxts)
    candidateStdAddress = map(lambda idxs: list(map(lambda i: ADDRESS_LIB[i], idxs)),
                              candidateStdAddressIndexs.values())
    candidateStdAddress = dict(zip(candidateStdAddressIndexs.keys(),
                                   candidateStdAddress))
    finalStdAddress = dict()
    a, b, c, d, e, f = 0, 0, 0, 0, 0, 0
    outputFileHandler = open(outputPath, 'w', encoding='utf-8')
    outputFileHandler.write('filename,label\n')
    print('start match ...')
    for index, candidates in candidateStdAddress.items():
        if len(candidates) == 0:
            # TODO: 1. no candidates
            a += 1
            print('{}.html'.format(index))
        street = addressTxts[index]['street']+addressTxts[index]['street_num']
        matchedStdAddress = standard_match(street, candidates)
        if matchedStdAddress is None:
            # TODO: no match at street+street_num
            b += 1
            matchedStdAddress = match_approximate_address(addressTxts[index],
                                                          candidates)
            if len(matchedStdAddress):
                finalStdAddress[index] = matchedStdAddress
            assert len(matchedStdAddress) == 1, 'multiple match: {}'.format(
                matchedStdAddress)
            for stdAddr in matchedStdAddress:
                # print("{}.html,{}".format(index, '$'.join(stdAddr.values())))
                outputFileHandler.write("{}.html,{}\n".format(
                    index, '$'.join(stdAddr.values())))
                f += 1
        elif isinstance(matchedStdAddress, list):
            # TODO: more info for match.
            # print(index, addressTxts[index], matchedStdAddress)
            print(index, 'more info need for match')
            outputFileHandler.write("{}.html,need more info.\n".format(index))
            c += 1
        elif isinstance(matchedStdAddress, dict):
            assert index not in finalStdAddress
            finalStdAddress[index] = matchedStdAddress
            # print("{}.html,{}".format(index, '$'.join(matchedStdAddress.values())))
            outputFileHandler.write("{}.html,{}\n".format(index, '$'.join(
                matchedStdAddress.values())))
            d += 1
        else:
            e += 1

    print('no candidate in First: {}\n'
          'Need approximate match: {}\n'
          'Multiple exactly match: {}\n'
          'Exactly match: {}\n'
          'Other: {}\n'
          'Approximate matched item: {}'.format(a, b, c, d, e, f))


def main():
    global ADDRESS_LIB, REVERSED_INDEX
    matchedAddressFilePath = 'data/result.csv'
    extractedAddressPath = 'data/auto_cut.txt'
    ADDRESS_LIB = load_standard_address(STANDARD_ADDRESS_LIB_PATH)
    REVERSED_INDEX = build_reversed_index(ADDRESS_LIB)
    match(extractedAddressPath, matchedAddressFilePath)


if __name__ == '__main__':
    main()
    t_end = time.time()
    print('time consume:', t_end - t_start)
