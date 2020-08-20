import jieba
from util import build_user_dict


def distance(item0, item1):
    """Pseudeo Euclidean Distance"""
    idx0X, idx0Y = (float(item0['locationx']),
                    float(item0['locationy']))
    idx1X, idx1Y = (float(item1['locationx']),
                    float(item1['locationy']))
    tmpDis = ((idx0X - idx1X)*10**4) ** 2 + ((idx0Y - idx1Y)*10**4) ** 2
    return tmpDis


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


def segment_address(addressTxts, reverseIndex=None):
    if reverseIndex:
        userDictPath = build_user_dict(reverseIndex)
        jieba.set_dictionary(userDictPath)
    addressSegs = list()
    for addressTxt in addressTxts:
        words = jieba.lcut(addressTxt, cut_all=False, HMM=0)
        addressSegs.append(words)
    return addressSegs
