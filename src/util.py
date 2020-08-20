# encoding=utf-8
import re
STANDARD_ADDRESS_LIB_PATH = 'data/位置信息识别-复赛数据/复赛标准地址库.csv'


def load_standard_address(path=None):
    if not path:
        path = STANDARD_ADDRESS_LIB_PATH
    addresses = list()
    fieldSeparator, lineSeparator = '\t', '\n'
    with open(path, 'r', encoding='utf-8') as f:
        fieldNames = f.readline().strip().split(fieldSeparator)
        for line in f:
            fieldValues = map(lambda x: x.strip(), line.split(fieldSeparator))
            addressItem = dict(zip(fieldNames, fieldValues))
            addresses.append(addressItem)
    return addresses


def build_reversed_index(addresses):
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
            if field in ['province', 'city']:
                if address[field][:-1] not in reIndex[field]:
                    reIndex[field][address[field][:-1]] = set()
                reIndex[field][address[field][:-1]].add(index)
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


def get_same_street_item(item, reversedIndex):
    feildNames = ['province', 'city', 'district', 'township', 'street']
    filterFeildValues = list(map(lambda x: (x, item[x]), feildNames))
    numIndexs = set()
    for field, value in filterFeildValues:
        fieldSet = reversedIndex[field][value]
        if not numIndexs:
            numIndexs = fieldSet
            continue
        numIndexs = numIndexs.intersection(fieldSet)
    return numIndexs


def get_first_num(numTxt):
    values = list(filter(len, re.split(r'[^\d]', numTxt)))
    return int(values[0])


if __name__ == "__main__":
    addresses = load_standard_address()
    reversedIndex = build_reversed_index(addresses)
    testCases = ['王圣堂莲塘街13号', '人民大道63号', '你不知道我知道']
    words = segment_address(testCases, reversedIndex)
    print(words)
