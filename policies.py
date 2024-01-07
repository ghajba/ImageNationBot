from nft import get_addresses, assets_for_address
from collections import Counter

adapes_policies = [
    '61326897a69a96ce77f5ddcbccc7f00404b8c10e21ab4bb9cb7e9f96',  # s2
    '304cae95a0326705b495da3ddd66826539eead4e693917fdf0860fa5',  # s3
    '7fec61f72b88c65d32e97e8039f611d58e7f7c50ff68f62ab8be1281',  # s4
]
abstractum_policies = [
    'ab6d24bf3b49fe8e7a82c35ad32acd4d8dd77efa54f3bd71fe7320c8',
    '97de7832c6a97a9436a0b6ad4aff4a22346888f7f34a3aea866c3a67',  # morphs
]

pantheon_policies = ['83746d1d6dbbc3349f0bd9c81e5322f855f0c4c27b539cf1b33a0774', ]

snek_warriors_policies = ['8cb5626a127d110fdbdb0085c933ba0721f5c67457b4d03f64f3502d', ]

pixel_frenz_policies = ['7ac7ea917de363dad11cade111ea6b8f0356a6ef4bc5f77f01b967f3', ]

xhg_policies = [
    'd8f6abf1fbbcabd4a28bfee0924013e2136b9ef719c2820172aa12f6',  # Yuletide
    'e495bb2457a91372f915031b1608d1342b2d504652fa3b352590dcc6',  # inktober 2023
    '3a6680bf43130830a9c1b02edaf82967b9c8408c4d50dd75c612f9ef'  # NSFWitches
]


def get_xhg_holders():
    global counts
    all_addresses = []
    for policy in xhg_policies:
        all_addresses += get_addresses(policy)
    counts = Counter(all_addresses)
    with open(f'addresses.txt', 'w') as outfile:
        outfile.write('\n'.join(all_addresses))


if __name__ == '__main__':
    for asset in assets_for_address('stake1uy0az42r6zz2dsk7xwcdatddcshd32tp5g7zg5wlu5acj9g0ds9z2'):
        if 'f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a' in asset['unit']:
            print(asset)
    # print(valid_address('$xhg'))
    # get_xhg_holders()
    #
    # with open('addresses.txt') as infile:
    #     addresses = [l.strip() for l in infile.readlines() if l.strip()]
    # counts = Counter(addresses)
    # for k, v in counts.items():
    #     if v >= 6:
    #         print(k, v)
    print(bytes.fromhex('706978656c6672656e7a').decode('utf-8'))
    print('gaborsketches'.encode('utf-8').hex())
    # print(bytes.fromhex('000de1406761626f72736b657463686573').decode('utf-8'))
    print(bytes.fromhex('636f696e6465706f').decode('utf-8'))
