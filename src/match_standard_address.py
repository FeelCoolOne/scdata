STANDARD_ADDRESS_LIB_PATH = 'data/位置信息识别-复赛数据/复赛标准地址库.csv'
ADDRESS_LIB = None


def load_addresses():
    addresses = list()
    fieldSeparator, lineSeparator = '\t', '\n'
    with open(STANDARD_ADDRESS_LIB_PATH, 'r', encoding='utf-8') as f:
        fieldNames = f.readline().rstrip(lineSeparator).split(fieldSeparator)
        for line in f:
            fieldValues = line.rstrip(lineSeparator).split(fieldSeparator)
            addressItem = dict(zip(fieldNames, fieldValues))
            addresses.append(addressItem)
    return addresses


def get_subAddress(feilds):
    subAddress = list(map(lambda x: x['street']+x['street_num'], ADDRESS_LIB))
    return subAddress


def match_street_plus_streetNum(addressTxt, candidates):
    matchedSubStdAddress = list(filter(
        lambda x: x[1] in addressTxt and len(x[1]),
        enumerate(candidates)))
    if len(matchedSubStdAddress) == 0:
        return None
    if len(matchedSubStdAddress) == 1:
        return matchedSubStdAddress[0][0]
    maxLen = max(map(lambda x: len(x[1]), matchedSubStdAddress))
    candidates = list(filter(lambda x: maxLen == x[1], matchedSubStdAddress))
    if len(candidates) == 1:
        return candidates[0][0]
    stdIdAddressTxts = list(map(lambda m: (m[0], addressTxt.replace(m[1], '')),
                                candidates))
    # TODO: check order of match field.
    priorityMatchField = ['township', 'district', 'city', 'province']
    return match_addition_field(priorityMatchField, stdIdAddressTxts)


def match_addition_field(fields, stdIdAddressTxts):
    candidateStdAddresses = map(lambda x: ADDRESS_LIB[x[0]], stdIdAddressTxts)
    addressTxts = stdIdAddressTxts
    for field in fields:
        subCandidates = filter(lambda a, c: c[field] in a[1],
                               zip(addressTxts, candidateStdAddresses))
        if len(subCandidates) == 0:
            continue
        if len(subCandidates) == 1:
            return subCandidates[0][0]
        assert len(subCandidates) > 1, "ValueError"
        addressTxts = map(lambda x: (x[0][0], x[0].replace(x[1][field], '')),
                          subCandidates)
        candidateStdAddresses = map(lambda x: ADDRESS_LIB[x[0][0]], subCandidates)

    raise ValueError('multiple sample in lib: {}'.format(stdIdAddressTxts))


def match_different_num(addressTxt, candidatesIdxs):
    pass


def match():
    extractedAddressPath = '../data/extracted_address_text_0727.txt'
    STREET_NUM_PAT = r'[\d\-之a-z][号栋座]'
    streetStreetNumAddress = get_subAddress(['street', 'street_num'])
    notSSNNum = 0
    with open(extractedAddressPath, 'r', encoding='utf-8') as f:
        for line in f:
            index, addressTxt = line.rstrip().split('-->')
            # [street+street_num] in addressTxt
            matchedSubStdAddress = list(filter(
                lambda x: x[1] in addressTxt and len(x[1]),
                enumerate(streetStreetNumAddress)))
            finalMatched = len(matchedSubStdAddress) == 1
            # match with max length common substring.
            if not finalMatched and len(matchedSubStdAddress):
                counter = dict()
                for addressIdx, subAddress in matchedSubStdAddress:
                    if len(subAddress) not in counter:
                        counter[len(subAddress)] = []
                    counter[len(subAddress)].append((addressIdx, subAddress))
                maxLen = max(counter.keys())
                maxLenComStringCandidate = counter[maxLen]
                finalMatched = len(maxLenComStringCandidate) == 1
                addressTxts = map(lambda x: (x[0], addressTxt.replace(x[1], '')),
                                  maxLenComStringCandidate)

            # match with additional text in addressTxt if avaiable candidates
            if not finalMatched and len(matchedSubStdAddress):
                extendCandidates = filter(lambda x: x[1] < len(addressTxt),
                                          matchedSubStdAddress)
                addressTxtAndCandidateIdxs = map(
                    lambda x: (x[0], addressTxt.replace(x[1], '')),
                    extendCandidates)
                priorityMatchField = ['township', 'district', 'city', 'province']
                tmpMatchedSubStdAddress = match_addition_field(
                    priorityMatchField, addressTxtAndCandidateIdxs)
                finalMatched = len(tmpMatchedSubStdAddress) == 1
            # need more info from html
            subStdAddressAbnomal = filter(lambda x: x[1] == len(addressTxt), matchedSubStdAddress)
            if finalMatched:
                continue
            notSSNNum += 1
            if len(matchedSubStdAddress):
                print(matchedSubStdAddress)
                print(addressTxt)
    print(notSSNNum)


def main():
    ADDRESS_LIB = load_addresses()