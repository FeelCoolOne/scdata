
from util import load_standard_address, build_reversed_index, segment_address

ADDRESS_LIB = None


def match_street_plus_streetNum(stdIdAddressTxts):
    candidateStdAddresses = map(lambda x: (
        ADDRESS_LIB[x[0]]['street'] + ADDRESS_LIB[x[0]]['street_num']),
        stdIdAddressTxts)
    idTxtCandts = map(lambda x, y: (x[0], x[1], y),
                      stdIdAddressTxts, candidateStdAddresses)
    matchedIdTxtCandts = list(filter(
        lambda x: x[2] in x[1] and len(x[2]), idTxtCandts))
    if len(matchedIdTxtCandts) == 0:
        return None  # street+street_num not in txt
    if len(matchedIdTxtCandts) == 1:
        return matchedIdTxtCandts[0][0]
    maxLen = max(map(lambda x: len(x[2]), matchedIdTxtCandts))
    maxLenIdTxtCandts = list(filter(lambda x: maxLen == len(x[2]),
                                    matchedIdTxtCandts))
    if len(maxLenIdTxtCandts) == 1:
        return maxLenIdTxtCandts[0][0]
    stdIdAddressTxts = map(lambda m: (m[0], m[1].replace(m[2], '')),
                           maxLenIdTxtCandts)
    stdIdAddressTxts = list(filter(lambda x: len(x[1]), stdIdAddressTxts))
    if len(stdIdAddressTxts) == 0:
        return -1  # multiple max length street+street_num in txt
    # TODO: check order of match field.
    priorityMatchField = ['township', 'district', 'city', 'province']
    return match_addition_field(priorityMatchField, stdIdAddressTxts)


def match_addition_field(fields, stdIdAddressTxts):
    candidateStdAddresses = list(map(lambda x: ADDRESS_LIB[x[0]], stdIdAddressTxts))
    addressTxts = stdIdAddressTxts
    for idx, field in enumerate(fields):
        # TODO: postfix(city, province, township et al.)
        subCandidates = list(filter(lambda x: x[1][field] in x[0][1],
                                    zip(addressTxts, candidateStdAddresses)))
        if len(subCandidates) == 0:
            continue
        if len(subCandidates) == 1:
            return subCandidates[0][0][0]
        assert len(subCandidates) > 1, "ValueError"
        addressTxts = map(lambda x: (x[0][0], x[0].replace(x[1][field], '')),
                          subCandidates)
        addressTxts = list(filter(lambda x: len(x[1]), addressTxts))
        if len(addressTxts) == 0:
            return -(idx+2)
        candidateStdAddresses = map(lambda x: ADDRESS_LIB[x[0][0]], subCandidates)

    raise ValueError('multiple sample in lib: {}'.format(stdIdAddressTxts))


def match_different_num(addressTxt, candidatesIdxs):
    pass


def search_candidate_stdAddress(segmentedAddressTxts, reversedIndex):
    candidateStdAdresses = dict()
    # TODO: check negative impact for ignore street_num.
    # ! default order may not be obey by sample.
    priorityFields = ['street', 'township', 'district', 'city', 'province']
    for index, segmentedAddressTxt in segmentedAddressTxts.items():
        candidates = set()
        for field in priorityFields:
            # TODO: check null string.
            fieldRelatedIndex = reversedIndex[field]
            tmpCandidate = set()
            for word in segmentedAddressTxt:
                tmpCandidate = tmpCandidate.union(fieldRelatedIndex.get(word, set()))
            if not tmpCandidate:
                continue
            if len(candidates):
                candidates = candidates.intersection(tmpCandidate)
            else:
                candidates = tmpCandidate
        candidateStdAdresses[index] = candidates
    return candidateStdAdresses


def match():
    extractedAddressPath = 'data/extracted_address_text_0727.txt'
    STREET_NUM_PAT = r'[\d\-之a-z][号栋座]'
    notSSNNum = 0
    addressTxts = dict()
    with open(extractedAddressPath, 'r', encoding='utf-8') as f:
        for line in f:
            index, addressTxt = line.rstrip().split('-->')
            assert index not in addressTxts, '{}'.format(index)
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

    # stdIdAddressTxts = list(enumerate([
    #     addressTxt for _ in range(len(ADDRESS_LIB))]))
    # matchedStandardAddressId = match_street_plus_streetNum(
    #     stdIdAddressTxts)
    # if matchedStandardAddressId and matchedStandardAddressId >= 0:
    #     print(index, addressTxt, ADDRESS_LIB[matchedStandardAddressId])
    #     continue
    # if matchedStandardAddressId is None:
    #     # no street+street_num match, variant for street_num
    #     pass
    # notSSNNum += 1
    # print(notSSNNum)


def main():
    global ADDRESS_LIB
    ADDRESS_LIB = load_standard_address()
    match()


if __name__ == '__main__':
    main()
