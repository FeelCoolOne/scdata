# encoding=utf-8
import jieba
import os
import pickle


def load_standard_address(path, rebuild=False, cache='data/sa.dat'):
    if os.path.isfile(cache) and not rebuild:
        with open(cache, 'rb') as f:
            addresses = pickle.load(f)
        return addresses
    addresses = list()
    fieldSeparator, lineSeparator = '\t', '\n'
    with open(path, 'r', encoding='utf-8') as f:
        fieldNames = f.readline().strip().split(fieldSeparator)
        for line in f:
            fieldValues = map(lambda x: x.strip(), line.split(fieldSeparator))
            addressItem = dict(zip(fieldNames, fieldValues))
            addresses.append(addressItem)
    with open(cache, 'wb') as f:
        pickle.dump(addresses, f)
    return addresses


def build_reversed_index(addresses, rebuild=False, cache='data/ri.dat'):
    if os.path.isfile(cache) and not rebuild:
        with open(cache, 'rb') as f:
            reIndex = pickle.load(f)
        return reIndex

    fieldNames = ['province', 'city', 'district', 'township', 'street',
                  'street_num']
    reIndex = {fn: dict() for fn in fieldNames}
    for index, address in enumerate(addresses):
        for field in fieldNames:
            assert field in address, '%s not in %s' % (field, address)
            if not address[field].strip():
                continue
            if address[field] not in reIndex[field]:
                reIndex[field][address[field]] = set()
            reIndex[field][address[field]].add(index)
            # if field in ['province', 'city']:
            #     if address[field][:-1] not in reIndex[field]:
            #         reIndex[field][address[field][:-1]] = set()
            #     reIndex[field][address[field][:-1]].add(index)
    with open(cache, 'wb') as f:
        pickle.dump(reIndex, f)
    return reIndex


def build_user_dict(reverseIndex, path='./data/addressUserDict.txt'):
    userDict = []
    for fn, fieldIndexList in reverseIndex.items():
        for value, indexList in fieldIndexList.items():
            if not len(value):
                continue
            value = value.replace(' ', '')
            userDict.append([value, len(indexList), 'n'])

    with open(path, 'w', encoding='utf-8') as f:
        for word, cnt, type_ in userDict:
            f.write(' '.join([word, str(cnt), type_]) + '\n')
            # f.write(''.join([word]) + '\n')
    return path


def segment_address(addressTxts, reverseIndex=None):
    if reverseIndex:
        userDictPath = build_user_dict(reverseIndex)
        jieba.set_dictionary(userDictPath)
    addressSegs = list()
    for addressTxt in addressTxts:
        words = jieba.lcut(addressTxt, cut_all=False, HMM=0)
        addressSegs.append(words)
    return addressSegs


if __name__ == "__main__":
    addresses = load_standard_address('data/位置信息-决赛数据/决赛标准地址库.csv')
    reversedIndex = build_reversed_index(addresses)
    testCases = ['王圣堂莲塘街13号', '人民大道63号', '你不知道我知道']
    words = segment_address(testCases, reversedIndex)
    print(words)
