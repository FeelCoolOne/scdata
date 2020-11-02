firstAAddressLibPath = './data/位置信息-初复赛地址库/测绘初赛地址库/初赛A榜标准地址库.csv'
firstBAddressLibPath = './data/位置信息-初复赛地址库/测绘初赛地址库/新B榜标准地址库.csv'
twiceAddressLibPath = './data/位置信息-初复赛地址库/复赛标准地址库.csv'
finalAddressLibPath = './data/位置信息-决赛数据/决赛标准地址库.csv'


def read_lines(path, sep='\t'):
    lines = set()
    with open(path, 'r', encoding='utf-8') as f:
        fieldNames = f.readline().strip().split(sep)
        for line in f:
            line = line.rstrip()
            fieldValues = map(lambda x: x.strip(), line.split(sep))
            line = '\t'.join(fieldValues)
            lines.add(line)
    return lines, fieldNames


def main():
    addressLines = set()
    lineCnt = 0
    paths = [(firstAAddressLibPath, '\t'), (firstBAddressLibPath, ','),
             (twiceAddressLibPath, '\t'), (finalAddressLibPath, '\t')]
    for path, sep in paths:
        lines, fieldNames = read_lines(path, sep)
        lineCnt += len(lines)
        addressLines = addressLines.union(lines)

    uniqueLineCnt = len(addressLines)
    allAddressLibPath = './data/address_library_all.csv'
    with open(allAddressLibPath, 'w', encoding='utf-8') as f:
        f.write('\t'.join(fieldNames)+'\n')
        for addressLine in addressLines:
            f.write(addressLine+'\n')

    print('line total: {}, unique line: {}'.format(lineCnt, uniqueLineCnt))
    print('Finished')


if __name__ == '__main__':
    main()
