def ad_check(filename):
    ad_keywords = [
        '微信', '独家', 'V信', 'v信', '威信',
        '加微', '会员群', 'q群', 'v群', '公众号',
        '广告', '特价', '最后机会', '不要错过', '立减',
        '立得', '赚', '省', '回扣', '抽奖'
    ]
    for keyword in ad_keywords:
        if keyword in filename:
            return True
    return False
