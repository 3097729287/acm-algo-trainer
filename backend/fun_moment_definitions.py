"""Fixed identities and rewards for the playful achievement collection."""
MOMENTS={
 'moment-rebound':dict(name='好，刚才不算',description='同一道题先收到错误回执，随后一小时内正式 AC',xp=15,hidden=False),
 'moment-semicolon':dict(name='; 救世主',description='一次 CE 后，只补上一个分号便正式 AC',xp=15,hidden=True),
 'moment-polyglot':dict(name='换种语言，照样拿下',description='同一道题分别使用 C++ 与 Python 正式 AC',xp=20,hidden=False),
 'moment-photo-finish':dict(name='压哨球',description='在模拟赛最后五秒发出的正式提交最终 AC',xp=20,hidden=True),
 'moment-clock':dict(name='数字排排坐',description='正式 AC 的提交时刻恰逢北京时间时、分、秒相同',xp=10,hidden=True),
 'moment-42':dict(name='宇宙终极答案',description='一次成功的自测运行只输出了 42',xp=10,hidden=True),
 'moment-gallery':dict(name='我这里有点热闹',description='同时摆放五张贴纸，布置自己的成长页',xp=15,hidden=False),
 'moment-rainbow':dict(name='一盒彩虹',description='库存中集齐普通、稀有、史诗、传说四种品质的贴纸',xp=20,hidden=False),
 'moment-upside-down':dict(name='倒立也很可爱',description='把一张贴纸旋转半圈后正式固定',xp=10,hidden=True),
 'moment-returned':dict(name='完璧归仓',description='确认回收一张已放置贴纸，让它回到库存',xp=10,hidden=False),
 'moment-wiki-trip':dict(name='算法旅行家',description='在维基中打开过三个不同分类的原始算法条目',xp=10,hidden=False),
 'moment-duel-tie':dict(name='心有灵犀',description='真实双人对战中，两人在同一秒提交并双双 AC',xp=25,hidden=True),
 'moment-duel-rebound':dict(name='先礼后兵',description='真实对战先出现未通过的尝试，仍率先 AC 赢得本场',xp=20,hidden=True),
 'moment-prophet':dict(name='我先说说',description='向当日榜首留言“就这?”后，自己获得该日已结算的第一名',xp=20,hidden=True),
}
