# encoding=utf-8
import re

from util import load_standard_address, build_reversed_index, segment_address

ADDRESS_LIB = None


def standard_match(addressTxt, candidateStdAddress):

    idSSCandts = map(lambda x: (x[0], x[1]['street']+x[1]['street_num']),
                     enumerate(candidateStdAddress))
    matchedIdSSCandts = list(filter(
        lambda x: x[1] in addressTxt and len(x[1]), idSSCandts))
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
    streetNumTxtValues = list(filter(len, re.split(r'[^\d]', streetNumTxt)))
    if not len(streetNumTxtValues):
        matchedIdxs, _ = filter_nearby_street_NonNum(streetNumTxt, streetNums)
        return matchedIdxs, list(map(lambda x: streetNums[x], matchedIdxs))

    idxStreetNumValues = list(map(
        lambda sn: (sn[0], list(filter(len, re.split(r'[^\d]', sn[1])))),
        enumerate(streetNums)))
    idxStreetNumValuesTMP = list(filter(
        lambda x: len(x[1]) > 0, idxStreetNumValues))
    assert len(idxStreetNumValuesTMP) > 1, '{} {}'.format(streetNumTxt, streetNums)

    streetNumFlag = int(streetNumTxtValues[0]) % 2
    idxStreetNumValuesTMP = list(filter(
        lambda x: int(x[1][0]) % 2 == streetNumFlag,
        idxStreetNumValuesTMP))
    if len(idxStreetNumValuesTMP) == 0:
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
    minLen = min(map(lambda x: len(x[1]), idxStreetNumValuesTMP))
    if minLen > len(streetNumTxtValues):
        matchedIdxs = list(map(lambda x: x[0], idxStreetNumValuesTMP))
        # 3# --> 3#1 3#9
        return matchedIdxs, list(map(lambda x: streetNums[x], matchedIdxs))

    indicator = max(minLen-1, idx)
    tmp = 2 if indicator == 0 else 1
    neighborNums = [int(num)+tmp, int(num)-tmp]
    neighbors, parents = set(), set()
    for idxTMP, numTMP in idxStreetNumValuesTMP:
        if len(numTMP) > indicator and int(numTMP[idx]) not in neighborNums:
            continue
        if len(numTMP) <= indicator:
            parents.add(idxTMP)
            continue
        neighbors.add(idxTMP)
    if len(neighbors):
        matchedIdxs = neighbors
        # 3#3 --> 3#2 3#4
        # 1# --> 3# 5#
        return matchedIdxs, list(map(lambda x: streetNums[x], matchedIdxs))

    idxStreetNumValuesTMP = list(filter(lambda x: len(x[1]) > indicator,
                                        idxStreetNumValuesTMP))
    if not idxStreetNumValuesTMP:
        matchedIdxs = parents
        # 3#3 --> 3#
        return matchedIdxs, list(map(lambda x: streetNums[x], matchedIdxs))
    # 3#3 --> [3#] 3#5 3#1
    # 3#
    tmp = list(filter(lambda x: len(x[1]) <= indicator, idxStreetNumValuesTMP))
    matchedIdxs = list(map(lambda x: x[0], tmp))
    downPoint, upPoint = None, None
    diffs = list(map(lambda x: (x[0], int(x[1][1][indicator]) - int(num)),
                     enumerate(idxStreetNumValuesTMP)))
    upDiffs = list(filter(lambda x: x[1] > 0, diffs))
    downDiffs = list(filter(lambda x: x[1] < 0, diffs))
    upValue = min(upDiffs, key=lambda x: x[1]) if upDiffs else 10000
    downValue = max(downDiffs, key=lambda x: x[1]) if downDiffs else -10000
    for i, diff in diffs:
        if diff not in [upValue, downValue]:
            continue
        matchedIdxs.append(idxStreetNumValuesTMP[i][0])
    return matchedIdxs, list(map(lambda x: streetNums[x], matchedIdxs))


def post_calculate_nearby_street(stdAddresses):
    keys = map(lambda x: re.search(r'\d+', x[1]['street_num']),
               stdAddresses)
    match = sorted(zip(stdAddresses, keys),
                   key=lambda x: int(x[1][0]) if x[1] is not None else 10**7)[0][0]
    return [match[0]], [match[1]]


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
    STREET_NUM_EXPR = r'[\d\-之附a-z#]+[号栋座]'
    streetNumTxt = re.search(STREET_NUM_EXPR, addressTxt)
    if streetNumTxt is None:
        matchedIdxs, _ = filter_nearby_street_NonNum(addressTxt,
                                                     streetNumCandts)
    else:
        streetNumTxt = streetNumTxt[0]
        matchedIdxs, _ = filter_nearby_streetNum(streetNumTxt, streetNumCandts)
    if len(matchedIdxs) > 1:
        matchedIdxs, _ = post_calculate_nearby_street(list(map(
            lambda x: (x, candidateStdAddress[x]), matchedIdxs)))
    return list(map(lambda x: candidateStdAddress[x], matchedIdxs))


def search_candidate_stdAddress(segmentedAddressTxts, reversedIndex,
                                fieldUnion=False):
    candidateStdAdresses = dict()
    # TODO: check negative impact for ignore street_num.
    # ! default order may not be obey by sample.
    priorityFields = ['street', 'township', 'district', 'city', 'province']
    for index, segmentedAddressTxt in segmentedAddressTxts.items():
        candidates = set()
        for field in priorityFields:
            fieldRelatedIndex = reversedIndex[field]
            tmpCandidate = set()
            for word in segmentedAddressTxt:
                tmpCandidate = tmpCandidate.union(fieldRelatedIndex.get(word, set()))
            if not tmpCandidate:
                continue
            if fieldUnion:
                candidates = candidates.union(tmpCandidate)
            else:
                candidates = candidates.intersection(tmpCandidate) if len(
                    candidates) else tmpCandidate
            if not candidates:
                break
        candidateStdAdresses[index] = candidates
    return candidateStdAdresses


def match():
    extractedAddressPath = 'data/extracted_address_text_0727.txt'
    notSSNNum = 0
    addressTxts = dict()
    with open(extractedAddressPath, 'r', encoding='utf-8') as f:
        for line in f:
            index, addressTxt = line.rstrip().split('-->')
            assert index not in addressTxts, '{}'.format(index)
            addressTxt = addressTxt.strip()
            if not addressTxt:
                continue
            addressTxts[index] = addressTxt

    reversedIndex = build_reversed_index(ADDRESS_LIB)
    segmentedAddressTxts = segment_address(addressTxts.values(),
                                           reversedIndex)
    segmentedAddressTxts = map(lambda x: list(filter(lambda y: len(y) > 1, x)),
                               segmentedAddressTxts)
    segmentedAddressTxts = dict(zip(addressTxts.keys(), segmentedAddressTxts))
    candidateStdAddressIndexs = search_candidate_stdAddress(
        segmentedAddressTxts, reversedIndex)
    candidateStdAddress = map(lambda idxs: list(map(lambda i: ADDRESS_LIB[i], idxs)),
                              candidateStdAddressIndexs.values())
    candidateStdAddress = dict(zip(candidateStdAddressIndexs.keys(),
                                   candidateStdAddress))
    finalStdAddress = dict()
    a, b, c = 0, 0, 0
    for index, candidates in candidateStdAddress.items():
        if len(candidates) == 0:
            # TODO: 1. no candidates
            a += 1
            pass
        matchedStdAddress = standard_match(addressTxts[index], candidates)
        if matchedStdAddress is None:
            # TODO: no match at street+street_num
            b += 1
            matchedStdAddress = match_approximate_address(addressTxts[index],
                                                          candidates)

            if len(matchedStdAddress):
                finalStdAddress[index] = matchedStdAddress
            for stdAddr in matchedStdAddress:
                print("{}.html,{}".format(index, '$'.join(stdAddr.values())))
            pass
        elif isinstance(matchedStdAddress, list):
            # TODO: more info for match.
            # print(index, addressTxts[index], matchedStdAddress)
            c += 1
            pass
        elif isinstance(matchedStdAddress, dict):
            assert index not in finalStdAddress
            finalStdAddress[index] = matchedStdAddress
    print(a, b, c)


def main():
    global ADDRESS_LIB
    ADDRESS_LIB = load_standard_address()
    match()


if __name__ == '__main__':
    main()
