import json, sys
SH = []


def I(k, x, y, **kw):
    d = dict(k=k, x=x, y=y)
    d.update(kw)
    return d


def F(k, **kw):
    d = dict(k=k)
    d.update(kw)
    return d


def S(start, bg, items, fx=(), **kw):
    d = dict(start=start, bg=bg, items=list(items), fx=list(fx))
    d.update(kw)
    SH.append(d)


# ---- intro (title + subtitle on top half only)
S(0, 'day', [I('sun', 860, 760, s=0.7, anim='breathe', **{'in': 0.4}), I('cloud', 250, 700, s=0.7, anim='drift', **{'in': 0.8}),
             I('hill', 540, 1430, how='grow', **{'in': 1.2}), I('sword', 560, 1160, s=0.62, how='grow', **{'in': 2.6}),
             I('grass', 250, 1540, s=0.8, **{'in': 3.2}), I('grass', 840, 1560, s=0.8, **{'in': 3.4})],
  [F('birds', at='drop', x=860, y=760, n=5), F('rays', at='drop', x=860, y=760, r0=110, r1=120, s=0.7, z='back'), F('leaves', at='drop', n=10)],
  cam=dict(z=[1.0, 1.04]))
# One page per two sung lines. Items of the second line enter on the same page; anything that
# would crowd them leaves (`out`) first. `tr` picks the page transition.
M = __import__('math')

# L1-2 他们笑我这把木剑 / 也敢拿来挡住苍天
S('L1-0.3', 'day', [I('cloud', 300, 420, s=0.7, anim='drift', out='L2', odur=0.8), I('cloud', 820, 300, s=0.5, anim='drift', out='L2', odur=0.8),
                    I('ground', 540, 1480, how='fade'), I('fence', 540, 1210, how='draw'),
                    I('crow', 250, 1060, s=1.0, anim='laugh', how='pop', out='L2', odur=0.3, **{'in': 'L1.1'}),
                    I('crow', 540, 1045, s=0.9, anim='laugh', flip=True, how='pop', out='L2', odur=0.3, **{'in': 'L1.3'}),
                    I('crow', 820, 1060, s=1.05, anim='laugh', how='pop', out='L2', odur=0.3, **{'in': 'L1.5'}),
                    I('sword', 540, 1470, s=0.62, rot=88, how='fade', out='L2.1', odur=0.3, **{'in': 'L1.7'}),
                    I('darkcloud', 540, -120, s=1.4, how='fade', to=[540, 300], move=['L2', 'L2.end'], **{'in': 'L2-0.2'}),
                    I('sword', 540, 1000, s=0.9, how='rise', anim='shake', amp=0.5, **{'in': 'L2.1'})],
  [F('birds', at='L2', x=540, y=1050, n=4), F('wind', at='L2', n=6), F('rays', at='L2.6', x=540, y=540, r0=60, r1=160, n=12)], tr='fade')
# L3-4 我说神力还没醒 / 先替天公管点人间
S('L3-0.3', 'night', [I('stars', 540, 520, s=1.0, n=14, anim='flicker'),
                      I('moon_sleep', 740, 420, s=0.95, anim='bob', how='fade', out='L4', odur=0.6),
                      I('ground', 540, 1500, col=(70, 100, 90)), I('tree', 250, 1150, s=0.95, col=(60, 120, 95), out='L4', odur=0.6),
                      I('sword', 560, 1330, s=0.55, rot=-80, how='fade', out='L4', odur=0.6, **{'in': 'L3.3'}),
                      I('palace', 540, 430, s=0.8, how='fall', **{'in': 'L4'}),
                      I('village', 540, 1380, s=0.95, lit=True, how='grow', **{'in': 'L4.2'}),
                      I('sword', 540, 700, s=0.35, rot=180, to=[540, 1000], move=['L4.4', 'L4.end'], how='fade', **{'in': 'L4.3'})],
  [F('bubbles', at='L3.4', end='L4', x=920, y=330), F('rays', at='L4', x=540, y=430, r0=240, r1=160, n=16, z='back', col=(250, 215, 120))], tr='iris', tr_at=(740, 420))
# L5-6 袖里藏着半包火药 / 掌心藏着一截红线
S('L5-0.3', 'indoor', [I('robe', 330, 760, s=1.0, how='draw'), I('pouch', 800, 700, s=0.7, how='pop', anim='bob', amp=0.4, **{'in': 'L5.4'}),
                       I('table', 540, 1400), I('spool', 720, 1170, s=0.9, how='pop', **{'in': 'L6.1'})],
  [F('sparks', at='L5.6', x=830, y=560, s=0.6),
   F('thread', at='L6.4', path=[[640, 1180], [520, 1120], [420, 1060], [330, 1000]], grow=1.4, w=8),
   F('sparks', at='L6.end-0.3', x=330, y=1000, s=0.5)], tr='dissolve')
# L7-8 一声雷响吓跑山贼 / 全村喊我活神仙
S('L7-0.3', 'night', [I('darkcloud', 540, 230, s=1.4, how='fade', out='L8-0.2', odur=1.0),
                      I('mountains', 540, 1330, col=(100, 105, 140), near=(90, 120, 95), out='L8', odur=0.6),
                      I('bandit_flag', 330, 1150, s=0.8, to=[260, 1330], rot_to=-70, move=['L7.4', 'L7.4+0.6'], out='L8', odur=0.5),
                      I('torch', 700, 1200, s=0.9, anim='shake', to=[1200, 1100], move=['L7.5', 'L7.end+0.4']),
                      I('torch', 820, 1250, s=0.8, anim='shake', to=[1250, 1180], move=['L7.5', 'L7.end+0.2']),
                      I('blade', 460, 1480, s=0.8, rot=-15, how='fade', out='L8', odur=0.5, **{'in': 'L7.5'}),
                      I('village', 540, 1320, lit=True, how='grow', **{'in': 'L8'}),
                      I('lantern', 180, 330, s=0.8, anim='swing', how='fall', **{'in': 'L8.2'}),
                      I('lantern', 900, 330, s=0.8, anim='swing', how='fall', **{'in': 'L8.3'})],
  [F('bolt', at='L7.3', x=560, y=720, s=0.9),
   F('footprints', at='L7.5', end='L7.end', path=[[380, 1560], [700, 1500], [1040, 1420]], n=9, col=(80, 60, 50)),
   F('fireworks', at='L8.1', hits='chars:L8'), F('lanterns', at='L8.3', n=6, gap=0.4, y=1100)], tr='zoom')
# L9-10 孩子追着问我姓名 / 我说天机不可外传
S('L9-0.3', 'dusk', [I('path', 540, 1180, how='grow'), I('tree', 170, 950, s=0.7), I('pine', 930, 900, s=0.8),
                     I('stick', 820, 1400, s=0.8, **{'in': 'L9.3'}), I('pinwheel', 820, 1270, s=0.9, anim='spin', how='pop', **{'in': 'L9.3'}),
                     I('xiangyun', 200, 300, s=0.5, anim='drift', amp=0.3, how='fade', **{'in': 'L10'}),
                     I('xiangyun', 880, 300, s=0.5, flip=True, how='fade', **{'in': 'L10'}),
                     I('scroll', 540, 520, s=1.2, how='pop', anim='bob', **{'in': 'L10.2'})],
  [F('footprints', at='L9', end='L9.end', path=[[560, 1600], [520, 1300], [470, 1000], [520, 760]], n=10, col=(120, 90, 60)),
   F('footprints', at='L9.2', end='L9.end+0.4', path=[[640, 1610], [600, 1320], [560, 1050]], n=12, s=0.6, col=(200, 90, 90)),
   F('glow', at='L10.2', x=540, y=520, r=340, z=7), F('sparks', at='L10.5', x=540, y=520, s=1.2)], tr='fade')
# L11-12 他把热饼塞进我手 / 说神仙也要吃晚饭
S('L11-0.3', 'indoor', [I('window', 540, 520, s=0.8, glass=(40, 55, 110), how='fade', **{'in': 'L12'}), I('crescent', 600, 480, s=0.4, how='fade', **{'in': 'L12.2'}),
                        I('table', 540, 1380), I('cloth', 540, 1230, s=1.2, how='draw'), I('bread', 540, 1140, s=1.3, how='rise', **{'in': 'L11.3'}),
                        I('bowl', 190, 1200, s=0.75, how='pop', **{'in': 'L12.3'}), I('bowl', 890, 1200, s=0.75, chopsticks=False, how='pop', **{'in': 'L12.5'})],
  [F('glow', at='L11.3', x=540, y=1140, r=420, col=(255, 200, 120), z='back'), F('steam', at='L11.4', x=540, y=1000, s=1.3),
   F('steam', at='L12.4', x=190, y=1120, s=0.7), F('steam', at='L12.6', x=890, y=1120, s=0.7)], tr='dissolve')
# L13-14 村口悬着一座吊桥 / 桥下深渊望不见边
S('L13-0.3', 'dusk', [I('abyss', 540, 1150, s=1.3), I('cliff_l', 170, 1000), I('cliff_r', 910, 1000),
                      I('house', 150, 420, s=0.5, c=0, lit=True), I('bridge', 540, 690, how='draw', **{'in': 'L13.2'})],
  [F('wind', at='L13.5', n=4), F('smoke', at='L14', x=540, y=1500, n=6, s=1.4, h=700, col=(90, 95, 130)),
   F('embers', at='L14.3', x=540, y=700, w=300, h=-900, n=10)], cam=dict(z=[1.0, 1.14], y=[-60, 260]), tr='iris', tr_at=(540, 300))
# L15-16 他问妖怪来了怎办 / 我说别怕有我在前
S('L15-0.3', 'dark', [I('monster', 540, 700, s=0.9, how='fade', a=0.75, dur=2.0, out='L16.4', odur=0.6, **{'in': 'L15.4'}),
                      I('pine', 150, 1250, col=(20, 40, 40)), I('pine', 360, 1330, s=0.8), I('pine', 760, 1320, s=0.85), I('pine', 950, 1240),
                      I('sword', 540, 1050, s=1.0, how='grow', anim='breathe', **{'in': 'L16.3'})],
  [F('eyes', at='L15.1', n=7, gap=0.25, x0=120, x1=960, y0=500, y1=1350, flee='L16.5'),
   F('glow', at='L16.4', x=540, y=1000, r=420, col=(255, 230, 140), z=4), F('rays', at='L16.5', x=540, y=700, r0=130, r1=320)], tr='dissolve')
# ---- chorus 1 (bold)
S('L17-0.3', 'dawn', [I('sun', 540, 560, s=1.4, how='rise'), I('xiangyun', 170, 800, s=0.6, anim='drift'), I('xiangyun', 900, 760, s=0.6, anim='drift', amp=-1),
                      I('peak', 540, 1380), I('sword', 540, 1000, s=0.9, how='grow', **{'in': 'L17.3'}, anim='sway', amp=0.4)],
  [F('rays', at='L17', x=540, y=560, r0=170, r1=260, z=1), F('birds', at='L18', x=540, y=900, n=7)], cam=dict(z=[1.0, 1.08]), tr='flash')
# L19-20 一把木剑一身破衫 / 也敢替你挡住黑天
S('L19-0.3', 'dusk', [I('village', 540, 1470, s=0.7, lit=True, how='fade', **{'in': 'L20'}),
                      I('sword', 330, 860, s=0.8, how='grow', **{'in': 'L19.1'}),
                      I('robe', 740, 900, s=0.8, how='draw', anim='sway', **{'in': 'L19.5'}),
                      I('darkcloud', 540, 20, s=1.6, how='fade', to=[540, 280], move=['L20', 'L20.5'], **{'in': 'L20-0.2'})],
  [F('wind', at='L19.6', n=5), F('leaves', at='L19.6', n=12), F('rays', at='L20.6', x=330, y=520, r0=60, r1=200, col=(255, 230, 120))], tr='zoom')
# L21-22 等我唤醒满身雷电 / 叫那妖邪跪在山前
S('L21-0.3', 'storm', [I('mountains', 540, 1100, s=1.0, col=(110, 100, 130), near=(100, 95, 120)),
                       I('darkcloud', 300, 250, s=1.1, out='L22', odur=0.8), I('darkcloud', 820, 200, s=1.0, seed=5, out='L22', odur=0.8),
                       I('peak', 540, 1420, s=1.0), I('sword', 540, 1080, s=1.0, anim='shake', amp=0.6),
                       I('shadow', 200, 1280, s=0.6, to=[200, 1470], move=['L22.3', 'L22.6'], a=0.9, how='fade', **{'in': 'L22'}),
                       I('shadow', 880, 1280, s=0.6, flip=True, to=[880, 1470], move=['L22.4', 'L22.7'], a=0.9, how='fade', **{'in': 'L22'})],
  [F('bolt', at='L21.3', x=420, y=620, hits=['L21.6'], s=0.8), F('glow', at='L21.3', x=540, y=900, r=360, col=(255, 235, 120), z=4),
   F('sparks', at='L21.4', x=540, y=720, s=1.6), F('rays', at='L22', x=540, y=640, r0=60, r1=160, n=12, z=4)], tr='flash')
# L23-24 你只管把饭煮好 / 等我回来再添一碗
S('L23-0.3', 'indoor', [I('stove', 290, 1380, s=0.75), I('pot', 290, 1160, s=0.75, how='fall'),
                        I('table', 780, 1420, s=0.5, how='fade', **{'in': 'L24-0.2'}),
                        I('bowl', 680, 1250, s=0.6, chopsticks=False, how='pop', **{'in': 'L24'}),
                        I('bowl', 890, 1250, s=0.6, rice=False, how='pop', out='L24.7', odur=0.3, **{'in': 'L24.3'}),
                        I('bowl', 890, 1250, s=0.6, how='fade', dur=0.5, **{'in': 'L24.7'})],
  [F('fire', at='L23', x=290, y=1470, s=0.4, z=0), F('steam', at='L23.3', x=290, y=950, s=1.2, n=4),
   F('steam', at='L24.2', x=680, y=1180, s=0.6), F('steam', at='L24.8', x=890, y=1180, s=0.6)], tr='dissolve')
# ---- verse 3 dark
# L25-26 那夜黑风翻过山岗 / 符纸燃尽化作青烟
S('L25-0.9', 'dark', [I('mountains', 540, 1200, col=(55, 55, 85), near=(40, 60, 60)),
                      I('pine', 200, 1380, anim='sway', amp=3), I('pine', 540, 1420, s=0.9, anim='sway', amp=3), I('pine', 880, 1380, anim='sway', amp=3),
                      I('darkcloud', -300, 300, s=1.2, to=[1500, 300], move=['L25-0.9', 'L26'], ease=False),
                      I('talisman', 540, 620, s=1.1, how='draw', out='L26.4', odur=0.3, **{'in': 'L26'}),
                      I('talisman', 540, 620, s=1.1, burnt=True, how='fade', dur=0.3, out='L26.end', odur=0.8, **{'in': 'L26.4'})],
  [F('wind', at='L25', n=12), F('leaves', at='L25', n=24),
   F('fire', at='L26.3', end='L26.end', x=540, y=830, s=0.7), F('smoke', at='L26.4', x=540, y=560, n=7, s=1.0, col=(120, 165, 150), h=500)], tr='fade')
# L27-28 我把火药点在坛前 / 只有几点微光明灭
S('L27-0.3', 'night', [I('altar', 540, 1200, s=1.1), I('pouch', 840, 1430, s=0.55, how='pop', out='L28.2', odur=1.0, **{'in': 'L27.3'})],
  [F('smoke', at='L27', x=540, y=930, n=3, s=0.4, h=400), F('sparks', at='L27.5', end='L28', x=866, y=1310, s=0.6),
   F('glow', at='L28', x=540, y=1150, r=260, col=(255, 200, 110), z='back'),
   F('fireflies', at='L28', n=9, x0=250, x1=830, y0=500, y1=900)], tr='iris', tr_at=(540, 1200))
# L29-30 邪魔一脚踏碎神坛 / 妖影森然侵入庭院
S('L29-0.3', 'dark', [I('crescent', 860, 250, s=0.45), I('gate', 540, 900, s=0.9),
                      I('altar', 540, 1340, s=0.8, out='L29.4', odur=0.1),
                      I('altar', 540, 1370, s=0.8, broken=True, how='fade', dur=0.1, **{'in': 'L29.4'}),
                      I('footprint', 540, 1000, s=1.0, how='drop', out='L29.end', odur=0.5, **{'in': 'L29.3'}),
                      I('shadow', 60, 950, s=0.8, to=[250, 950], move=['L30', 'L30.end'], a=0.8, how='fade', **{'in': 'L30'}),
                      I('shadow', 1020, 950, s=0.8, flip=True, to=[830, 950], move=['L30.2', 'L30.end'], a=0.8, how='fade', **{'in': 'L30.2'})],
  [F('shake', at='L29.4', amp=1.3), F('smoke', at='L29.4', end='L29.end', x=540, y=1450, n=6, s=1.2, h=300, col=(110, 90, 80)),
   F('eyes', at='L30.3', n=4, x0=200, x1=880, y0=380, y1=620)], tr='dissolve')
# L31-32 我横剑独立门前 / 背上鲜血浸透衣衫
S('L31-0.3', 'night', [I('gate', 540, 1000, s=0.9, out='L32', odur=0.8),
                       I('sword', 540, 1300, s=1.0, rot=90, how='fade', out='L32', odur=0.8, **{'in': 'L31.2'}),
                       I('robe', 540, 860, s=1.3, how='fade', dur=0.8, **{'in': 'L32'}),
                       I('robe', 540, 860, s=1.3, blood=True, how='fade', dur=2.0, **{'in': 'L32.3'})],
  [F('eyes', at='L31-0.3', n=6, gap=0.05, x0=120, x1=960, y0=300, y1=620, flee='L31.5'), F('glow', at='L31.3', end='L32', x=540, y=1300, r=300, z=1),
   F('rain', at='L32', n=70)], cam=dict(z=[1.0, 1.06]), tr='zoom')
# ---- verse 4 wounded
# L33-34 待到天明风声渐歇 / 我已伤卧草榻之间
S('L33-0.5', 'indoor', [I('window', 540, 520, s=1.0, glass=(250, 225, 170)),
                        I('bed', 500, 1250, s=0.9, how='fade', **{'in': 'L34-0.2'}),
                        I('bandage', 250, 1500, s=0.7, how='pop', **{'in': 'L34.4'}), I('sword', 960, 1260, s=0.5, rot=12, how='fade', **{'in': 'L34.2'})],
  [F('rays', at='L33', x=540, y=520, r0=240, r1=150, n=10, z='back', col=(250, 230, 160)), F('birds', at='L33.4', x=540, y=460, n=3)], tr='fade')
# L35-36 孩子守在榻边 / 他将红线递到跟前
S('L35-0.3', 'indoor', [I('bed', 580, 1320, s=0.8), I('shoes', 580, 1540, s=0.7, how='pop', **{'in': 'L35.2'}),
                        I('stick', 140, 1300, s=0.7), I('pinwheel', 140, 1170, s=0.7, anim='spin', amp=0.2, how='pop', **{'in': 'L35.4'}),
                        I('spool', 540, 720, s=1.2, how='rise', **{'in': 'L36.2'})],
  [F('glow', at='L36.3', x=540, y=720, r=340, col=(255, 150, 140), z='back'),
   F('thread', at='L36.5', path=[[640, 760], [720, 900], [640, 1060], [560, 1180]], grow=1.2, w=8)], tr='dissolve')
# L37-38 红线缠了一遍一遍 / 也换不来神力乍现
S('L37-0.3', 'indoor', [I('sword', 540, 1000, s=0.9, rot=90), I('knot', 330, 1000, s=0.55, how='pop', **{'in': 'L37.1'}),
                        I('knot', 540, 1000, s=0.55, how='pop', **{'in': 'L37.4'}), I('knot', 750, 1000, s=0.55, how='pop', **{'in': 'L37.7'})],
  [F('thread', at='L37', path=[[100, 1500], [300, 1250], [330, 1000], [540, 1000], [750, 1000], [900, 1150]], grow=2.5, w=6),
   F('sparks', at='L38.4', end='L38.4+0.4', x=540, y=1000, s=0.5), F('smoke', at='L38.5', x=560, y=950, n=3, s=0.5, h=300)],
  cam=dict(z=[1.0, 1.1]), tr='iris', tr_at=(540, 1000))
# L39-40 他说纸鹤尚能飞远 / 我却无颜与他相见
S('L39-0.3', 'indoor', [I('window', 540, 700, s=1.1, how='fade', out='L40', odur=0.8),
                        I('window', 540, 700, s=1.1, shut=True, how='fade', **{'in': 'L40'}),
                        I('crane', 200, 1350, s=0.9, to=[560, 620], move=['L39', 'L39.end'], anim='bob', out='L39.end', odur=0.6),
                        I('candle', 200, 1400, s=0.8, how='fade', **{'in': 'L40.2'}), I('sword', 900, 1300, s=0.55, rot=10)],
  [F('wind', at='L39.2', end='L40', n=3), F('fire', at='L40.2', x=200, y=1320, s=0.28), F('smoke', at='L40.4', x=200, y=1250, n=3, s=0.4, h=300)], tr='fade')
# ---- chorus 2 (fragile)
S('L41-0.3', 'night', [I('crescent', 820, 330, s=0.55), I('frost', 540, 1500), I('sword', 540, 1250, s=0.6, anim='tremble', amp=0.8)],
  [F('snow', at='L41', n=60), F('wind', at='L42', n=4)], tr='fade')
S('L43-0.3', 'night', [I('stars', 540, 600, n=18, anim='flicker'), I('moon', 160, 380, s=0.55, to=[900, 330], move=['L43', 'L44.end'], ease=False),
                       I('bandage', 470, 1250, s=1.3, how='draw'), I('candle', 870, 1300, s=0.8)],
  [F('fire', at='L43-0.3', x=870, y=1220, s=0.28), F('tears', at='L44', x=470, y=1330)], tr='dissolve')
# L45-46 也许再等一道雷电 / 也许还差一次磨练
S('L45-0.3', 'night', [I('darkcloud', 540, 330, s=1.0, a=0.8), I('whetstone', 540, 1320, s=1.3, how='fade', **{'in': 'L46-0.2'}),
                       I('sword', 540, 1200, s=0.75, rot=90, anim='saw', amp=0.9, how='fade', **{'in': 'L46'})],
  [F('bolt', at='L45.5', x=880, y=520, s=0.35), F('wind', at='L45', n=4), F('sparks', at='L46.2', x=540, y=1250, s=0.8)], tr='fade')
S('L47-0.3', 'dark', [I('sword', 540, 950, s=1.2, anim='shake', amp=0.5), I('knot', 540, 1320, s=0.6), I('knot', 540, 1230, s=0.5)],
  [F('embers', at='L47', x=540, y=1500, w=400, h=1200, n=30), F('glow', at='L48', x=540, y=500, r=180, col=(255, 200, 90), z=0)], cam=dict(z=[1.0, 1.14]), tr='zoom')
# ---- verse 5
# L49-50 天亮有人上山查看 / 遍地脚印绕过火焰
S('L49-1.0', 'dawn', [I('mountains', 540, 650, s=1.0), I('sun', 850, 380, s=0.6), I('path', 540, 1250, s=1.0),
                      I('stick', 480, 1270, s=0.6, rot=60, how='fade', **{'in': 'L50-0.3'}), I('stick', 600, 1270, s=0.6, rot=-60, how='fade', **{'in': 'L50-0.3'})] +
  [I('footprint', 540 + 330 * M.cos(a), 1230 + 220 * M.sin(a), s=0.2, rot=a * 57.3 + 90, how='fade', dur=0.2,
     **{'in': f'L50+{k * 0.25:.2f}'}) for k, a in enumerate([3.4 + 0.45 * j for j in range(9)])],
  [F('footprints', at='L49', end='L49.end+0.5', path=[[600, 1600], [560, 1300], [480, 1050], [520, 900]], n=12, col=(120, 90, 60)),
   F('fire', at='L50-0.3', x=540, y=1250, s=0.8), F('embers', at='L50', x=540, y=1200, w=100, h=500, n=12)], tr='iris', tr_at=(850, 380))
# L51-52 它们原来只怕亮光 / 躲进林中等着夜晚
S('L51-0.3', 'dusk', [I('lantern', 540, 600, s=1.5, anim='swing', amp=0.3, out='L52', odur=0.8),
                      I('shadow', 300, 1250, s=0.8, to=[-150, 1300], move=['L51.3', 'L51.end']),
                      I('shadow', 780, 1250, s=0.8, flip=True, to=[1230, 1300], move=['L51.3', 'L51.end']),
                      I('sun', 540, 700, s=1.1, how='fade', to=[540, 1150], move=['L52', 'L52.end+0.5'], **{'in': 'L52'}),
                      I('pine', 130, 1250, col=(40, 70, 60), how='grow', **{'in': 'L52'}), I('pine', 330, 1330, s=0.85, how='grow', **{'in': 'L52.1'}),
                      I('pine', 540, 1280, how='grow', **{'in': 'L52.2'}), I('pine', 750, 1330, s=0.85, how='grow', **{'in': 'L52.3'}),
                      I('pine', 950, 1250, how='grow', **{'in': 'L52.4'})],
  [F('glow', at='L51', end='L52', x=540, y=600, r=520, col=(255, 210, 110), z='back'), F('rays', at='L51.3', end='L52', x=540, y=600, r0=180, r1=260, z='back'),
   F('eyes', at='L52.4', n=6, gap=0.2, x0=120, x1=960, y0=1200, y1=1450)], tr='dissolve')
# L53-54 我翻遍了残破天书 / 末页写着戏法三篇
S('L53-0.3', 'indoor', [I('book', 540, 1000, s=1.15, torn=True, how='fade', out='L54', odur=0.5),
                        I('book', 540, 950, s=1.2, tricks=True, how='draw', **{'in': 'L54'}), I('candle', 900, 1400, s=0.8)],
  [F('fire', at='L53-0.3', x=900, y=1320, s=0.28), F('pages', at='L53.2', end='L54', x=400, y=1000, n=4),
   F('glow', at='L54.4', x=540, y=950, r=560, col=(255, 230, 150), z='back'), F('sparks', at='L54.5', x=540, y=700, s=1.2)], tr='fade')
# L55-56 引雷不过硝石一把 / 飞剑不过细丝一线
S('L55-0.3', 'night', [I('crystals', 300, 1400, s=0.9, how='pop', **{'in': 'L55.4'}),
                       I('tree', 700, 450, s=0.9, bare=True, col=(90, 70, 60), how='fade', **{'in': 'L56-0.3'}),
                       I('sword', 705, 1050, s=0.6, rot=90, anim='sway', amp=2.5, how='fade', **{'in': 'L56.3'})],
  [F('sparks', at='L55.5', x=300, y=1330, s=1.0), F('bolt', at='L55.7', x=300, y=850, s=0.6),
   F('thread', at='L56.4', path=[[720, 330], [705, 1050]], grow=0.8, w=3, col=(230, 230, 240))], tr='zoom')
# ---- breakdown
# L57-58 我松开那根线 / 木剑落在我的脚边
S('L57-0.3', 'night', [I('tree', 540, 450, s=1.0, bare=True),
                       I('sword', 540, 1100, s=0.85, rot=90, to=[520, 1480], rot_to=70, move=['L57.4', 'L57.4+0.5'], ease=False)],
  [F('thread', at='L57-0.3', end='L57.4', path=[[560, 330], [545, 1100]], grow=0.1, w=3, col=(230, 230, 240)),
   F('smoke', at='L57.4+0.5', end='L58.end', x=520, y=1520, n=4, s=0.6, h=150, col=(150, 130, 110)), F('leaves', at='L58', n=8)],
  cam=dict(z=[1.0, 1.12], y=[0, 300]), tr='fade')
# L59-60 没有祥云前来接我 / 只有风吹那本残卷
S('L59-0.3', 'dusk', [I('hill', 540, 1450), I('xiangyun', 540, 520, s=1.0, how='fade', out='L59.4', odur=1.2),
                      I('book', 540, 1350, s=0.7, torn=True, how='fade', **{'in': 'L60-0.3'})],
  [F('birds', at='L59.5', x=300, y=800, n=1), F('wind', at='L59.3', n=3),
   F('pages', at='L60', x=450, y=1300, n=6), F('wind', at='L60', n=6), F('leaves', at='L60', n=10)], tr='dissolve')
S('L61-0.3', 'dark', [I('stars', 540, 600, n=10, anim='flicker'), I('altar', 540, 1340, s=1.0, broken=True),
                      I('palace', 540, 500, s=0.8, a=0.45, how='fade', out='L62.3', odur=1.5)],
  [F('smoke', at='L61.5', x=540, y=1200, n=3, s=0.5, h=500)], tr='fade')
# L63-64 他们把命交给了我 / 我拿什么还给人间
S('L63-0.3', 'night', [I('village', 540, 1250, s=0.9, lit=True, how='fade', out='L64', odur=1.2),
                       I('ground', 540, 1500, col=(80, 100, 110), how='fade', **{'in': 'L64'}),
                       I('bowl', 540, 1300, s=1.3, rice=False, chopsticks=False, how='fade', **{'in': 'L64.2'}),
                       I('sword', 880, 1300, s=0.5, rot=15, how='fade', **{'in': 'L64.4'})],
  [F('lanterns', at='L63', end='L64.3', n=10, gap=0.25, y=1150, rise=5.0), F('rain', at='L64', n=90)], tr='iris', tr_at=(540, 1250))
# ---- bridge quiet
# L65-66 我趁黄昏收好行囊 / 想从后山逃得远远
S('L65-0.5', 'dusk', [I('sun', 190, 450, s=0.6, to=[190, 760], move=['L65', 'L66.end']), I('mountains', 540, 700, col=(130, 110, 150)), I('path', 540, 1250),
                      I('robe', 300, 1150, s=0.7, a=0.9, out='L66', odur=0.6),
                      I('bundle', 620, 1150, s=1.1, how='pop', to=[520, 950], move=['L66', 'L66.end+0.5'], **{'in': 'L65.4'})],
  [F('footprints', at='L66', end='L66.end', path=[[620, 1600], [560, 1300], [520, 1000]], n=9, col=(120, 90, 60))], tr='fade')
# L67-68 却见家家搀老抱小 / 挤在桥头不敢向前
S('L67-0.3', 'dusk', [I('bridge', 540, 650, s=0.9), I('cart', 280, 1330, s=0.9, how='fade'),
                      I('basket', 640, 1420, how='pop', **{'in': 'L67.3'}), I('basket', 850, 1380, s=0.85, how='pop', **{'in': 'L67.5'}),
                      I('lantern', 160, 1020, s=0.7, anim='swing'), I('lantern', 700, 1080, s=0.6, anim='swing'),
                      I('bundle', 920, 1150, s=0.5, how='pop', **{'in': 'L67.6'})],
  [F('eyes', at='L68.4', n=3, x0=700, x1=1000, y0=420, y1=560)], tr='dissolve')
# L69-70 孩子没有求我施法 / 只把热饼递到跟前
S('L69-0.3', 'dusk', [I('stick', 250, 1250, s=1.0), I('pinwheel', 250, 1070, s=1.0, anim='spin', amp=0.25), I('shoes', 250, 1490, s=0.7),
                      I('cloth', 680, 1200, s=1.0, how='draw', **{'in': 'L70'}), I('bread', 680, 1110, s=1.2, how='rise', **{'in': 'L70.4'})],
  [F('wind', at='L69.3', n=3), F('steam', at='L70.5', x=680, y=980, s=1.2), F('glow', at='L70.4', x=680, y=1110, r=420, col=(255, 200, 120), z='back')], tr='fade')
# ---- build
# L71-72 我沉默地站在桥前 / 任晚风吹过双肩
S('L71-0.3', 'dusk', [I('sun', 840, 330, s=0.6), I('abyss', 540, 1000, s=1.0), I('bridge', 540, 700, s=1.0),
                      I('ground', 540, 1490), I('sword', 540, 1200, s=0.95, how='grow', **{'in': 'L71.3'})],
  [F('wind', at='L72', n=8), F('leaves', at='L72', n=14)], cam=dict(z=[1.0, 1.08]), tr='zoom')
# L73-74 我低头吃完那张饼 / 把剩下的火药点燃
S('L73-0.3', 'night', [I('cloth', 330, 1200, s=1.0, out='L74', odur=0.6), I('bread', 330, 1110, s=1.2, out='L73.4', odur=0.1),
                       I('bread', 330, 1110, s=1.2, bite=True, how='fade', dur=0.1, out='L74', odur=0.6, **{'in': 'L73.4'}),
                       I('pouch', 540, 1000, s=1.3, anim='shake', amp=0.4, how='fade', **{'in': 'L74'})],
  [F('sparks', at='L74.3', x=590, y=640, s=1.2), F('fire', at='L74.7', x=590, y=660, s=0.5),
   F('glow', at='L74.3', x=540, y=900, r=500, col=(255, 150, 60), z='back')], tr='fade')
# ---- crescendo
# L75-76 这回没有神仙 / 只有我站在你们前面
S('L75-0.3', 'fire', [I('abyss', 540, 900, s=1.0), I('bridge', 540, 650, s=1.0), I('ground', 540, 1500, col=(90, 70, 60)),
                      I('darkcloud', 300, 250, s=1.2, to=[-300, 250], move=['L75.2', 'L76']),
                      I('darkcloud', 800, 280, s=1.2, seed=7, to=[1400, 280], move=['L75.2', 'L76']),
                      I('sword', 540, 1180, s=1.15, how='grow', **{'in': 'L76.2'})],
  [F('wind', at='L75', n=6), F('eyes', at='L76', n=8, gap=0.15, x0=120, x1=960, y0=200, y1=480),
   F('rays', at='L76.6', x=540, y=750, r0=150, r1=300, col=(255, 200, 90))], tr='dissolve')
# ---- chorus 3 (tragic)
S('L77-0.3', 'fire', [I('abyss', 540, 1000, s=1.0), I('bridge', 540, 700, s=1.0), I('sword', 540, 1150, s=1.0)],
  [F('fire', at='L77.2', x=540, y=1480, s=1.1, z=2), F('embers', at='L77', x=540, y=1500, w=500, h=1300, n=40)], tr='flash')
# L79-80 一把木剑一身破衫 / 曾经骗过多少双眼
S('L79-0.3', 'dusk', [I('village', 540, 1420, s=0.8, lit=True, how='fade', **{'in': 'L80'}),
                      I('sword', 330, 850, s=0.8), I('robe', 740, 850, s=0.85, blood=True, anim='sway')],
  [F('embers', at='L79', x=540, y=1500, w=500, h=1300, n=20), F('wind', at='L79', n=4),
   F('fireflies', at='L80', n=12, x0=150, x1=930, y0=200, y1=450)], tr='zoom')
# L81-82 没有雷霆应我召唤 / 没有飞剑替我向前
S('L81-0.3', 'storm', [I('darkcloud', 540, 330, s=1.4), I('peak', 540, 1420),
                       I('sword', 540, 1080, s=1.0, to=[540, 1440], rot_to=84, move=['L82.2', 'L82.2+0.6'])],
  [F('sparks', at='L81.4', end='L81.4+0.3', x=540, y=640, s=0.4), F('wind', at='L81', n=5),
   F('thread', at='L82', path=[[560, 500], [555, 900]], grow=0.1, w=3, col=(230, 230, 240))], tr='fade')
# L83-84 你领众人渡过桥去 / 那碗饭也不用再添
S('L83-0.3', 'night', [I('abyss', 540, 1100, s=1.0, out='L84-0.2', odur=0.8), I('cliff_l', 130, 1150, s=0.9, out='L84-0.2', odur=0.8),
                       I('cliff_r', 950, 1150, s=0.9, out='L84-0.2', odur=0.8), I('bridge', 540, 830, out='L84-0.2', odur=0.8),
                       I('lantern', 120, 850, s=0.45, anim='swing', to=[1000, 850], move=['L83', 'L83.end+1'], ease=False, out='L84-0.2', odur=0.8),
                       I('lantern', 0, 870, s=0.45, anim='swing', to=[880, 870], move=['L83.2', 'L83.end+1'], ease=False, out='L84-0.2', odur=0.8),
                       I('lantern', -120, 850, s=0.45, anim='swing', to=[760, 850], move=['L83.4', 'L83.end+1'], ease=False, out='L84-0.2', odur=0.8),
                       I('table', 540, 1360, how='fade', **{'in': 'L84.3'}), I('bowl', 540, 1150, s=1.1, how='fade', **{'in': 'L84.3'}),
                       I('candle', 870, 1100, s=0.8, how='fade', **{'in': 'L84.3'})],
  [F('smoke', at='L84.5', x=870, y=950, n=3, s=0.4, h=300), F('steam', at='L84.5', x=540, y=1070, s=0.9)], tr='dissolve')
# ---- final chorus
# L85-86 神仙在此 / 谁敢向前
S('L85-1.2', 'fire', [I('abyss', 540, 1100, s=1.0), I('bridge', 540, 800, s=1.0, burning=True, how='fade'),
                      I('monster', 540, 380, s=0.7, how='fade', dur=0.4, **{'in': 'L86'}),
                      I('sword', 540, 950, s=0.8, anim='shake', amp=0.6)],
  [F('boom', at='L85.1', x=540, y=700, s=1.3), F('rays', at='L85.1', x=540, y=650, r0=200, r1=420, z='back', col=(255, 200, 80)),
   F('embers', at='L85', x=540, y=1500, w=500, h=1400, n=50), F('shake', at='L86.1', amp=1.2, hits=['L86.3'])], tr='flash')
# L87-88 有胆就来 / 取我命还
S('L87-0.3', 'fire', [I('pouch', 540, 900, s=1.0, out='L87.2', odur=0.1),
                      I('monster', 540, 420, s=0.75, how='fade', to=[540, 1500], move=['L88.2', 'L88.end+0.4'], **{'in': 'L87.4'}),
                      I('bridge', 540, 1100, s=1.0, burning=True, how='fade', to=[540, 1350], rot_to=12, move=['L88.2', 'L88.end'], **{'in': 'L87.4'}),
                      I('sword', 540, 1000, s=0.9, how='rise', anim='shake', amp=0.5, **{'in': 'L88.1'})],
  [F('boom', at='L87.2', x=540, y=900, s=1.6, hits=['L87.4']), F('fireworks', at='L87.2', hits='chars:L87'),
   F('boom', at='L88.1', x=540, y=800, s=1.2, hits=['L88.3']), F('rays', at='L88.2', x=540, y=700, r0=180, r1=420, z='back', col=(255, 210, 90)),
   F('embers', at='L87', x=540, y=1500, w=500, h=1400, n=60)], tr='flash')
S('L88.end+0.4', 'dawn', [I('cliff_l', 170, 1150), I('cliff_r', 910, 1150), I('abyss', 540, 1330, s=1.0, a=0.8)],
  [F('smoke', at='L88.end+0.4', x=540, y=1400, n=7, s=1.5, h=1000, col=(160, 150, 150)), F('embers', at='L88.end+0.4', x=540, y=1400, w=300, h=900, n=12)], tr='fade')
# ---- outro
# L89-90 后来村口立了石像 / 一碗热饭摆在像前
S('L89-0.3', 'dawn', [I('ground', 540, 1490), I('house', 190, 1300, s=0.6, c=0), I('house', 890, 1300, s=0.6, c=2),
                      I('stele', 540, 1050, s=1.0, how='grow', dur=1.5), I('bowl', 540, 1480, s=0.8, how='pop', **{'in': 'L90.3'})],
  [F('steam', at='L90.4', x=540, y=1400, s=0.8)], tr='dissolve')
# L91-92 人人说他法力无边 / 只身挡下一场霜寒
S('L91-0.3', 'dawn', [I('sun', 850, 350, s=0.55, col=(240, 200, 170), how='fade', **{'in': 'L92'}),
                      I('lantern', 180, 330, s=0.7, anim='swing', out='L92', odur=0.8), I('lantern', 900, 330, s=0.7, anim='swing', out='L92', odur=0.8),
                      I('stele', 540, 1030, s=1.1), I('incense', 300, 1440, s=0.9), I('incense', 780, 1440, s=0.9),
                      I('frost', 540, 1500, how='grow', **{'in': 'L92'})],
  [F('rays', at='L91.3', end='L92', x=540, y=700, r0=250, r1=250, z='back'), F('smoke', at='L91', x=300, y=1330, n=3, s=0.4, h=500),
   F('smoke', at='L91', x=780, y=1330, n=3, s=0.4, h=500), F('snow', at='L92', n=50)], tr='fade')
# L93-94 风吹木剑响空山 / 月落桥头霜满肩
S('L93-0.3', 'night', [I('moon', 800, 300, s=0.8, to=[860, 700], move=['L93', 'L94.end+0.8']),
                       I('mountains', 540, 1100, col=(90, 90, 130), near=(70, 90, 100)), I('peak', 540, 1420),
                       I('sword', 540, 1090, s=0.8), I('chime', 620, 830, s=0.55, anim='swing', amp=1.5, out='L94', odur=0.6),
                       I('robe', 540, 1000, s=0.55, a=0.9, how='fade', **{'in': 'L94.2'}), I('frost', 540, 1560, how='grow', **{'in': 'L94'})],
  [F('wind', at='L93', end='L94', n=6), F('leaves', at='L93', end='L94', n=8), F('snow', at='L94', n=30)], tr='iris', tr_at=(800, 300))
# L95-96 无人知他去了哪边 / 炊烟又起在人间
S('L95-0.3', 'dawn', [I('path', 540, 1250, out='L96-0.3', odur=1.0), I('signpost', 850, 1100, s=0.8, out='L96-0.3', odur=1.0),
                      I('sun', 540, 700, s=1.0, how='rise', **{'in': 'L96-0.3'}), I('village', 540, 1300, lit=False, how='fade', **{'in': 'L96-0.3'}),
                      I('grass', 250, 1560, **{'in': 'L96'}), I('grass', 850, 1560, **{'in': 'L96'})],
  [F('smoke', at='L95', end='L96-0.3', x=540, y=900, n=6, s=2.0, h=500, col=(235, 230, 235)),
   F('footprints', at='L95', end='L95.end', path=[[560, 1600], [540, 1300], [520, 1050]], n=8, col=(120, 90, 60), a=0.5),
   F('smoke', at='L96', x=236, y=1030, n=4, s=0.35, h=600), F('smoke', at='L96.2', x=446, y=980, n=4, s=0.35, h=600),
   F('smoke', at='L96.4', x=656, y=1040, n=4, s=0.35, h=600), F('smoke', at='L96.6', x=876, y=970, n=4, s=0.35, h=600),
   F('birds', at='L96.end', x=540, y=800, n=5)], cam=dict(z=[1.0, 1.08]), tr='dissolve')

out = sys.argv[1]
old = json.load(open(out, encoding='utf-8'))
ev = [e for e in old.get('events', []) if e['type'] == 'lyricfx']
json.dump(dict(shots=SH, events=ev), open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(SH), 'shots')
