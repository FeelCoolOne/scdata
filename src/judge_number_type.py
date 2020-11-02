from util import (load_standard_address, build_reversed_index,
                  get_same_street_item, get_first_num)
from calculation import distance
import math

ADDRESS_LIB = load_standard_address()
REVERSED_INDEX = build_reversed_index(ADDRESS_LIB)


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
                candidates = candidates.union(fieldCandidates)
            else:
                candidates = candidates.intersection(fieldCandidates) if len(
                    candidates) else fieldCandidates
            if not candidates:
                break
        candidateStdAdresses[index] = candidates
    return candidateStdAdresses


def search_nearest_address_location(location, withInStreet, includeZero=False):
    """Search nearest address by Pseudeo Euclidean Distance in location.
    """
    indexs = get_same_street_item(withInStreet, REVERSED_INDEX)
    centerPoint = {'locationx': location[0], 'locationy': location[1]}
    visualDis = list(map(lambda idx: (idx, distance(ADDRESS_LIB[idx],
                                                    centerPoint)),
                     indexs))
    if not includeZero:
        visualDis = list(filter(lambda pair: not math.isclose(pair[1], 0.),
                                visualDis))
    minDis = min(visualDis, key=lambda x: x[1])[1]
    nearestPoints = list(map(lambda y: y[0],
                         filter(lambda x: math.isclose(x[1], minDis),
                                visualDis)))
    return nearestPoints


extractedAddressPath = 'data/extracted_formated_address_0810.txt'
addressTxts = dict()
with open(extractedAddressPath, 'r', encoding='utf-8') as f:
    for line in f:
        index, addressTxt = line.rstrip().split('-->')
        addressTxt = eval(addressTxt)
        assert index not in addressTxts, '{}'.format(index)
        if not addressTxt:
            raise Exception('{} {}'.format(index, addressTxt))
        addressTxts[index] = addressTxt

candidateStdAddressIndexs = search_candidate_stdAddress(addressTxts)

conCNT, pairCNT = 0, 0
for key, candtsIdxs in candidateStdAddressIndexs.items():
    item = ADDRESS_LIB[list(candtsIdxs)[0]]
    itemidxs = get_same_street_item(item, REVERSED_INDEX)
    contNum, pairNum, sameNum, other = 0, 0, 0, 0
    for idx in itemidxs:
        try:
            num = get_first_num(ADDRESS_LIB[idx]['street_num'])
            location = (ADDRESS_LIB[idx]['locationx'], ADDRESS_LIB[idx]['locationy'])
            addressIdxs = search_nearest_address_location(location, item, False)
            sNum = get_first_num(ADDRESS_LIB[addressIdxs[0]]['street_num'])
        except Exception as _:
            continue
        diff = abs(num - sNum)
        if diff == 1:
            contNum += 1
        elif diff == 2:
            pairNum += 1
        elif diff == 0:
            sameNum += 1
        else:
            other += 1
    print('continue num: {}\tpairNum: {}\tsameNum: {}\tother: {}'.format(
        contNum, pairNum, sameNum, other))
    if contNum > pairNum:
        conCNT += 1
    else:
        pairCNT += 1
print(conCNT, pairCNT)
