from util import load_standard_address, build_reversed_index
import json


def count_blur_matched_address(address, addresses, reversedIndex):
    candidateStdAdresses = dict()
    fieldWeight = [0.14, 0.13, 0.12, 0.11]
    priorityFields = ['street', 'township', 'district', 'city', 'province']
    candidates = set()
    for field in priorityFields:
        fieldRelatedIndex = reversedIndex[field]
        fieldValue = address.get(field, None)
        if not fieldValue:
            continue
        fieldCandidates = fieldRelatedIndex.get(fieldValue, set())
        candidates = candidates.intersection(fieldCandidates) if len(
            candidates) else fieldCandidates
        if not candidates:
            break
    streetNum = address.get('street_num', None)
    # TODO: check
    if streetNum in reversedIndex['province'] or streetNum in reversedIndex['city']:
        return 100000
    numSet = set(map(lambda i: addresses[i]['street_num'], candidates))
    if streetNum in numSet:
        cnt = 2  # default num-match score
        fieldScore = sum(map(lambda x: x[1] if x[0] in address else 0,
                             zip(priorityFields, fieldWeight)))
        return cnt - fieldScore
    return len(candidates)


def correct_address(address, reversedIndex):
    candidateStdAdresses = dict()
    priorityFields = ['street', 'township', 'district', 'city', 'province']
    candidates = set()
    for field in priorityFields:
        fieldRelatedIndex = reversedIndex[field]
        fieldValue = address.get(field, None)
        if not fieldValue:
            continue
        fieldCandidates = fieldRelatedIndex.get(fieldValue, set())
        candidatesTMP = candidates.intersection(fieldCandidates) if len(
            candidates) else fieldCandidates
        if not candidatesTMP:
            address.pop(field)
            continue
        candidates = candidatesTMP
    return address


def remove_address_noise(contentAddressPath, sep='-->', stdAddressLib=None,
                         reversedIndex=None, debug=False):
    if debug:
        print('start remove noisy-address...')
    articleRelatedAddress = dict()
    rawRecordCnt = 0
    with open(contentAddressPath, 'r',  encoding='utf-8') as f:
        for line in f:
            rawRecordCnt += 1
            sampleId, addressCandts = line.split(sep)
            sampleId = sampleId.rstrip('.html')
            addressCandts = eval(addressCandts)
            assert isinstance(addressCandts, list) and len(addressCandts) != 0
            addressCandts = list(map(
                lambda x: json.dumps(correct_address(x, reversedIndex)),
                addressCandts))
            addressCandts = list(map(lambda x: json.loads(x), set(addressCandts)))
            if len(addressCandts) == 1:
                if debug and rawRecordCnt < 10:
                    print('<<<<{}'.format(line.strip()))
                    print('>>>>{}\t{}'.format(sampleId, addressCandts[0]))
                # print('{}-->{}'.format(sampleId, addressCandts[0]))
                articleRelatedAddress[sampleId] = addressCandts[0]
                continue
            validScore = list(map(
                lambda x: count_blur_matched_address(x, stdAddressLib,
                                                     reversedIndex),
                addressCandts))
            validAdrs = sorted(zip(validScore, addressCandts), key=lambda x: x[0])
            if debug and rawRecordCnt < 10:
                print('<<<<{}'.format(line.strip()))
                print('>>>>{}\t{}'.format(sampleId, validAdrs[0][1]))

            articleRelatedAddress[sampleId] = validAdrs[0][1]
    if debug:
        print('remove-noise:: rawRecord {}, finalRecord {}'.format(
            rawRecordCnt, len(articleRelatedAddress)))
    return articleRelatedAddress
