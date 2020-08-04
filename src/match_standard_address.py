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
        matchedIdx, _ = filter_nearby_street_NonNum(streetNumTxt, streetNums)
        return matchedIdx, list(map(lambda x: streetNums[x], matchedIdx))

    idxStreetNumValues = list(map(
        lambda sn: (sn[0], list(filter(len, re.split(r'[^\d]', sn[1])))),
        enumerate(streetNums)))
    idxStreetNumValuesTMP = list(filter(lambda x: len(x[1]),
                                        idxStreetNumValues))
    for idx, num in enumerate(streetNumTxtValues):
        num = int(num)
        matchedNumIdx, minDistance = list(), 10**6
        # TODO: check the impact (1&9 - 1&1 > 1&9 - 1)
        distances = map(lambda x: (x[0], abs(int(x[1][idx]) - num)) if len(
                            x[1]) >= idx+1 else (x[0], 10**5),
                        idxStreetNumValuesTMP)
        for i, dis in distances:
            if dis < minDistance:
                minDistance = dis
                matchedNumIdx = [i]
            elif dis == minDistance:
                matchedNumIdx.append(i)
            else:
                continue
        assert len(matchedNumIdx) >= 1
        if len(matchedNumIdx) >= 2:
            idxStreetNumValuesTMP = list(map(lambda x: idxStreetNumValues[x],
                                             matchedNumIdx))
            continue
        return matchedNumIdx, [streetNums[matchedNumIdx[0]]]
    return matchedNumIdx, list(map(lambda x: streetNums[x], matchedNumIdx))


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
    return list(map(lambda x: candidateStdAddress[x], matchedIdxs))


def search_candidate_stdAddress(segmentedAddressTxts, reversedIndex):
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
            # print(index, addressTxts[index], matchedStdAddress)
            pass
        elif isinstance(matchedStdAddress, list):
            # TODO: more info for match.
            print(index, addressTxts[index], matchedStdAddress)
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
