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
# L1 他们笑我这把木剑
S('L1-0.3', 'day', [I('ground', 540, 1480, how='fade'), I('fence', 540, 1210, how='draw'),
                    I('crow', 250, 1060, s=1.0, anim='laugh', how='pop', **{'in': 'L1.1'}),
                    I('crow', 540, 1045, s=0.9, anim='laugh', flip=True, how='pop', **{'in': 'L1.3'}),
                    I('crow', 820, 1060, s=1.05, anim='laugh', how='pop', **{'in': 'L1.5'}),
                    I('sword', 540, 1470, s=0.62, rot=88, how='slide_l', **{'in': 'L1.7'}),
                    I('cloud', 300, 420, s=0.7, anim='drift'), I('cloud', 820, 300, s=0.5, anim='drift')])
# L2 也敢拿来挡住苍天
S('L2-0.3', 'storm', [I('peak', 540, 1380, how='grow'),
                      I('darkcloud', 540, 170, s=1.5, to=[540, 420], move=['L2', 'L2.end']),
                      I('sword', 540, 930, s=0.9, how='rise', **{'in': 'L2.2'}, anim='shake', amp=0.5)],
  [F('rays', at='L2.6', x=540, y=520, r0=60, r1=160, n=12, z=1), F('wind', at='L2', n=6)], cam=dict(z=[1.0, 1.08]))
# L3 我说神力还没醒
S('L3-0.3', 'night', [I('stars', 540, 520, s=1.0, n=14, anim='flicker'), I('moon_sleep', 740, 420, s=0.95, anim='bob', how='fade'),
                      I('ground', 540, 1500, col=(70, 100, 90)), I('tree', 250, 1150, s=0.95, col=(60, 120, 95)),
                      I('sword', 520, 1300, s=0.55, rot=-14, how='fade', **{'in': 'L3.3'})],
  [F('bubbles', at='L3.4', x=920, y=330)])
# L4 先替天公管点人间
S('L4-0.3', 'dawn', [I('palace', 540, 430, s=0.9, how='fall'), I('xiangyun', 190, 620, s=0.6, anim='drift', amp=-0.6), I('xiangyun', 880, 560, s=0.55, anim='drift'),
                     I('village', 540, 1380, s=0.95, lit=False, how='grow', **{'in': 'L4.3'}),
                     I('sword', 540, 720, s=0.35, rot=180, to=[540, 1020], move=['L4.4', 'L4.end'], how='fade', **{'in': 'L4.3'})],
  [F('rays', at='L4', x=540, y=400, r0=260, r1=180, n=16, z='back', col=(250, 215, 120))])
# L5 袖里藏着半包火药
S('L5-0.3', 'indoor', [I('robe', 470, 900, s=1.45, how='draw'), I('pouch', 830, 1140, s=0.75, how='slide_r', **{'in': 'L5.4'}, anim='bob', amp=0.4)],
  [F('sparks', at='L5.6', x=868, y=930, s=0.7)], cam=dict(z=[1.0, 1.1], x=[0, 120], y=[0, 120]))
# L6 掌心藏着一截红线
S('L6-0.3', 'indoor', [I('table', 540, 1330), I('spool', 330, 1070, s=1.1, how='pop', **{'in': 'L6.2'})],
  [F('thread', at='L6.5', path=[[420, 1110], [560, 980], [700, 1060], [820, 900], [960, 820]], grow=1.6, w=8),
   F('sparks', at='L6.end-0.3', x=960, y=820, s=0.5)])
# L7 一声雷响吓跑山贼
S('L7-0.3', 'storm', [I('darkcloud', 540, 230, s=1.4, how='fade'), I('mountains', 540, 1330, col=(100, 105, 140), near=(90, 120, 95)),
                      I('bandit_flag', 330, 1150, s=0.8, to=[260, 1330], rot_to=-70, move=['L7.4', 'L7.4+0.6']),
                      I('torch', 700, 1200, s=0.9, anim='shake', to=[1200, 1100], move=['L7.5', 'L7.end+0.4']),
                      I('torch', 820, 1250, s=0.8, anim='shake', to=[1250, 1180], move=['L7.5', 'L7.end+0.2']),
                      I('blade', 460, 1480, s=0.8, rot=-15, how='fade', **{'in': 'L7.5'})],
  [F('bolt', at='L7.3', x=560, y=720, s=0.9), F('footprints', at='L7.5', end='L7.end', path=[[380, 1560], [700, 1500], [1040, 1420]], n=9, col=(80, 60, 50))])
# L8 全村喊我活神仙
S('L8-0.3', 'dusk', [I('village', 540, 1320, lit=True, how='grow'),
                     I('lantern', 180, 330, s=0.8, anim='swing', how='fall'), I('lantern', 900, 330, s=0.8, anim='swing', how='fall'),
                     I('drum', 200, 1500, s=0.6, how='pop', **{'in': 'L8.2'}, anim='pulse', amp=3), I('gong', 880, 1490, s=0.55, how='pop', **{'in': 'L8.4'}, anim='pulse', amp=3)],
  [F('fireworks', at='L8.1', hits='chars:L8'), F('lanterns', at='L8.3', n=6, gap=0.4, y=1100)])
# L9 孩子追着问我姓名
S('L9-0.3', 'day', [I('path', 540, 1180, how='grow'), I('tree', 170, 950, s=0.7), I('pine', 930, 900, s=0.8),
                    I('stick', 820, 1400, s=0.8, **{'in': 'L9.3'}), I('pinwheel', 820, 1270, s=0.9, anim='spin', how='pop', **{'in': 'L9.3'})],
  [F('footprints', at='L9', end='L9.end', path=[[560, 1600], [520, 1300], [470, 1000], [520, 760]], n=10, col=(120, 90, 60)),
   F('footprints', at='L9.2', end='L9.end+0.4', path=[[640, 1610], [600, 1320], [560, 1050]], n=12, s=0.6, col=(200, 90, 90))])
# L10 我说天机不可外传
S('L10-0.3', 'night', [I('stars', 540, 700, n=22, anim='flicker'), I('xiangyun', 230, 1150, s=0.6), I('xiangyun', 850, 1180, s=0.6, flip=True),
                       I('scroll', 540, 860, s=1.5, how='pop', anim='bob', **{'in': 'L10.2'})],
  [F('glow', at='L10.2', x=540, y=860, r=380, z=2), F('sparks', at='L10.5', x=540, y=860, s=1.4)])
# L11 他把热饼塞进我手
S('L11-0.3', 'dusk', [I('cloth', 540, 1230, s=1.4, how='draw'), I('bread', 540, 1130, s=1.5, how='rise', **{'in': 'L11.3'})],
  [F('steam', at='L11.4', x=540, y=1010, s=1.4), F('glow', at='L11.3', x=540, y=1130, r=420, col=(255, 200, 120), z='back')], cam=dict(z=[1.0, 1.1]))
# L12 说神仙也要吃晚饭
S('L12-0.3', 'indoor', [I('window', 540, 560, s=0.9, glass=(40, 55, 110)), I('crescent', 600, 500, s=0.45),
                        I('table', 540, 1360), I('bowl', 360, 1150, s=0.9, how='pop', **{'in': 'L12.3'}), I('bowl', 720, 1150, s=0.9, how='pop', **{'in': 'L12.5'}, chopsticks=False),
                        I('candle', 900, 1100, s=0.8)],
  [F('fire', at='L12-0.3', x=900, y=1020, s=0.28), F('steam', at='L12.4', x=360, y=1080, s=0.8), F('steam', at='L12.6', x=720, y=1080, s=0.8)])
# L13 村口悬着一座吊桥
S('L13-0.3', 'dusk', [I('abyss', 540, 1330, s=1.0), I('cliff_l', 170, 1140), I('cliff_r', 910, 1140),
                      I('house', 150, 560, s=0.55, c=0, lit=True), I('bridge', 540, 830, how='draw', **{'in': 'L13.2'})],
  [F('wind', at='L13.5', n=4)], cam=dict(z=[1.0, 1.04], y=[0, -40]))
# L14 桥下深渊望不见边
S('L14-0.3', 'dark', [I('abyss', 540, 1000, s=1.6), I('cliff_l', 110, 900, s=0.9), I('cliff_r', 970, 900, s=0.9),
                      I('bridge', 540, 260, s=0.9, how='fade')],
  [F('smoke', at='L14', x=540, y=1500, n=7, s=1.6, h=900, col=(90, 95, 130)),
   F('embers', at='L14.3', x=540, y=300, w=300, h=-1200, n=12)], cam=dict(z=[1.0, 1.18], y=[0, 200]))
# L15 他问妖怪来了怎办
S('L15-0.3', 'dark', [I('monster', 540, 900, s=1.05, how='fade', a=0.75, dur=2.0, **{'in': 'L15.4'}),
                      I('pine', 150, 1250, col=(20, 40, 40)), I('pine', 360, 1330, s=0.8), I('pine', 760, 1320, s=0.85), I('pine', 950, 1240)],
  [F('eyes', at='L15.1', n=7, gap=0.25, x0=120, x1=960, y0=500, y1=1350)])
# L16 我说别怕有我在前
S('L16-0.3', 'dusk', [I('ground', 540, 1500), I('bridge', 540, 700, s=0.8, lanterns=True), I('village', 540, 1330, s=0.55),
                      I('sword', 540, 1180, s=1.05, how='grow', **{'in': 'L16.4'}, anim='breathe')],
  [F('rays', at='L16.5', x=540, y=800, r0=130, r1=320, z=3), F('eyes', at='L16-0.3', n=5, gap=0.1, x0=120, x1=960, y0=260, y1=560, flee='L16.5')])
# ---- chorus 1 (bold)
S('L17-0.3', 'dawn', [I('sun', 540, 560, s=1.4, how='rise'), I('xiangyun', 170, 800, s=0.6, anim='drift'), I('xiangyun', 900, 760, s=0.6, anim='drift', amp=-1),
                      I('peak', 540, 1380), I('sword', 540, 1000, s=0.9, how='grow', **{'in': 'L17.3'}, anim='sway', amp=0.4)],
  [F('rays', at='L17', x=540, y=560, r0=170, r1=260, z=1), F('birds', at='L18', x=540, y=900, n=7)], cam=dict(z=[1.0, 1.08]))
S('L19-0.3', 'day', [I('ground', 540, 1480), I('sword', 330, 1000, s=0.95, how='grow', **{'in': 'L19.1'}),
                     I('robe', 740, 1000, s=1.0, how='draw', anim='sway', **{'in': 'L19.5'})],
  [F('wind', at='L19.6', n=5), F('leaves', at='L19.6', n=12)])
S('L20-0.3', 'storm', [I('village', 540, 1400, lit=True), I('darkcloud', 540, 200, s=1.6, to=[540, 450], move=['L20', 'L20.5']),
                       I('sword', 540, 740, s=1.05, rot=90, how='rise', **{'in': 'L20.4'}, anim='shake', amp=0.6)],
  [F('rays', at='L20.6', x=540, y=740, r0=80, r1=220, z=2, col=(255, 230, 120))])
S('L21-0.3', 'storm', [I('darkcloud', 300, 250, s=1.1), I('darkcloud', 820, 200, s=1.0, seed=5), I('peak', 540, 1420, s=1.0),
                       I('sword', 540, 1080, s=1.0, anim='shake', amp=0.6)],
  [F('bolt', at='L21.3', x=420, y=620, hits=['L21.6'], s=0.8), F('glow', at='L21.3', x=540, y=900, r=360, col=(255, 235, 120), z=3),
   F('sparks', at='L21.4', x=540, y=720, s=1.6)])
S('L22-0.3', 'dusk', [I('mountains', 540, 1100, s=1.0, col=(150, 110, 150), near=(120, 100, 130)), I('peak', 540, 1400, s=0.9),
                      I('sword', 540, 1060, s=0.45),
                      I('shadow', 200, 1300, s=0.6, to=[200, 1470], move=['L22.3', 'L22.6'], a=0.9),
                      I('shadow', 880, 1300, s=0.6, to=[880, 1470], move=['L22.4', 'L22.7'], a=0.9)],
  [F('rays', at='L22', x=540, y=880, r0=40, r1=120, n=12, z=2)])
S('L23-0.3', 'indoor', [I('stove', 540, 1380, s=1.1), I('pot', 540, 1060, s=1.0, how='fall')],
  [F('fire', at='L23', x=540, y=1480, s=0.55, z=0), F('steam', at='L23.3', x=540, y=880, s=1.6, n=4)])
S('L24-0.3', 'indoor', [I('table', 540, 1360), I('bowl', 360, 1150, s=0.95, chopsticks=False),
                        I('bowl', 720, 1150, s=0.95, rice=False, how='pop', **{'in': 'L24.3'}),
                        I('bowl', 720, 1150, s=0.95, how='fade', **{'in': 'L24.7'}, dur=0.6), I('candle', 930, 1080, s=0.7)],
  [F('fire', at='L24-0.3', x=930, y=1010, s=0.25), F('steam', at='L24.7', x=720, y=1080, s=0.8), F('steam', at='L24', x=360, y=1080, s=0.8)])
# ---- verse 3 dark
S('L25-0.9', 'dark', [I('mountains', 540, 1200, col=(55, 55, 85), near=(40, 60, 60)),
                      I('pine', 200, 1380, anim='sway', amp=3), I('pine', 540, 1420, s=0.9, anim='sway', amp=3), I('pine', 880, 1380, anim='sway', amp=3),
                      I('darkcloud', 0, 300, s=1.2, to=[1100, 360], move=['L25-0.9', 'L25.end+1'], ease=False)],
  [F('wind', at='L25', n=12), F('leaves', at='L25', n=24)])
S('L26-0.3', 'night', [I('talisman', 540, 900, s=1.5, how='draw', out='L26.4', odur=0.3),
                       I('talisman', 540, 900, s=1.5, burnt=True, how='fade', dur=0.3, **{'in': 'L26.4'}, out='L26.end', odur=0.8)],
  [F('fire', at='L26.3', end='L26.end', x=540, y=1150, s=0.8), F('smoke', at='L26.4', x=540, y=800, n=7, s=1.0, col=(120, 165, 150), h=700)])
S('L27-0.3', 'night', [I('altar', 540, 1200, s=1.1), I('pouch', 840, 1430, s=0.55, how='pop', **{'in': 'L27.3'})],
  [F('smoke', at='L27', x=540, y=930, n=3, s=0.4, h=400), F('sparks', at='L27.5', x=866, y=1310, s=0.6)])
S('L28-0.3', 'dark', [I('altar', 540, 1250, s=1.0, a=0.35, how='fade')],
  [F('glow', at='L28', x=540, y=1150, r=260, col=(255, 200, 110), z='back'), F('fireflies', at='L28', n=9, x0=250, x1=830, y0=700, y1=1300), F('sparks', at='L28.3', x=820, y=1380, s=0.4)])
S('L29-0.3', 'dark', [I('altar', 540, 1300, s=1.0, out='L29.4', odur=0.1),
                      I('altar', 540, 1340, s=1.0, broken=True, how='fade', dur=0.1, **{'in': 'L29.4'}),
                      I('footprint', 540, 930, s=1.2, how='drop', **{'in': 'L29.3'})],
  [F('shake', at='L29.4', amp=1.3), F('smoke', at='L29.4', end='L29.end', x=540, y=1450, n=6, s=1.2, h=300, col=(110, 90, 80))])
S('L30-0.3', 'night', [I('crescent', 860, 280, s=0.5), I('gate', 540, 1150, s=1.0),
                       I('shadow', 150, 1300, s=0.9, to=[330, 1260], move=['L30', 'L30.end'], a=0.85),
                       I('shadow', 930, 1300, s=0.9, flip=True, to=[760, 1260], move=['L30.2', 'L30.end'], a=0.85)],
  [F('eyes', at='L30.3', n=4, x0=200, x1=880, y0=400, y1=700)])
S('L31-0.3', 'night', [I('gate', 540, 1050, s=0.95), I('sword', 540, 1300, s=1.05, rot=90, how='slide_l', **{'in': 'L31.2'})],
  [F('eyes', at='L31-0.3', n=6, gap=0.05, x0=120, x1=960, y0=300, y1=700, flee='L31.5'), F('glow', at='L31.3', x=540, y=1300, r=300, z=1)])
S('L32-0.3', 'night', [I('robe', 540, 900, s=1.45), I('robe', 540, 900, s=1.45, blood=True, how='fade', dur=2.0, **{'in': 'L32.3'})],
  [F('rain', at='L32', n=70)], cam=dict(z=[1.0, 1.08]))
# ---- verse 4 wounded
S('L33-0.5', 'dawn', [I('sun', 540, 1250, s=1.3, to=[540, 850], move=['L33-0.5', 'L33.end']), I('hill', 540, 1400), I('grass', 280, 1500), I('grass', 800, 1520)],
  [F('birds', at='L33.4', x=540, y=900, n=4), F('leaves', at='L33', n=6)])
S('L34-0.3', 'indoor', [I('window', 820, 500, s=0.7, glass=(230, 225, 190)), I('bed', 520, 1240, s=1.1),
                        I('bandage', 250, 1480, s=0.7, how='pop', **{'in': 'L34.4'}), I('sword', 930, 1260, s=0.55, rot=12)],
  [F('rays', at='L34', x=820, y=500, r0=160, r1=150, n=10, z='back', col=(250, 230, 160))])
S('L35-0.3', 'indoor', [I('bed', 520, 1180, s=1.0), I('shoes', 620, 1500, s=0.9, how='pop', **{'in': 'L35.2'}),
                        I('stick', 200, 1330, s=0.8, rot=10), I('pinwheel', 180, 1200, s=0.8, anim='spin', amp=0.2), I('candle', 900, 1400, s=0.8)],
  [F('fire', at='L35-0.3', x=900, y=1320, s=0.28)])
S('L36-0.3', 'indoor', [I('spool', 540, 900, s=1.6, how='rise', **{'in': 'L36.2'})],
  [F('glow', at='L36.3', x=540, y=900, r=380, col=(255, 150, 140), z='back'),
   F('thread', at='L36.5', path=[[700, 900], [800, 1100], [620, 1300], [540, 1560]], grow=1.2, w=8)], cam=dict(z=[1.0, 1.12]))
S('L37-0.3', 'indoor', [I('sword', 540, 1000, s=1.15, rot=90), I('knot', 330, 1000, s=0.55, how='pop', **{'in': 'L37.1'}),
                        I('knot', 540, 1000, s=0.55, how='pop', **{'in': 'L37.4'}), I('knot', 750, 1000, s=0.55, how='pop', **{'in': 'L37.7'})],
  [F('thread', at='L37', path=[[100, 1500], [300, 1250], [330, 1000], [540, 1000], [750, 1000], [900, 1150]], grow=2.5, w=6)])
S('L38-0.3', 'night', [I('crescent', 850, 320, s=0.5, a=0.6), I('sword', 540, 1000, s=1.15, rot=90),
                       I('knot', 330, 1000, s=0.55), I('knot', 540, 1000, s=0.55), I('knot', 750, 1000, s=0.55)],
  [F('sparks', at='L38.4', end='L38.4+0.4', x=540, y=1000, s=0.5), F('smoke', at='L38.5', x=560, y=950, n=3, s=0.5, h=300)])
S('L39-0.3', 'day', [I('mountains', 540, 1330), I('cloud', 250, 420, s=0.7, anim='drift'), I('cloud', 850, 650, s=0.55, anim='drift'),
                     I('crane', 180, 1250, s=0.9, to=[880, 380], move=['L39', 'L39.end+0.8'], anim='bob')],
  [F('wind', at='L39.2', n=3)])
S('L40-0.3', 'indoor', [I('window', 540, 820, s=1.15, shut=True, how='fade'), I('sword', 900, 1300, s=0.55, rot=10), I('candle', 220, 1400, s=0.8)],
  [F('smoke', at='L40.4', x=220, y=1250, n=3, s=0.4, h=300)], cam=dict(z=[1.08, 1.0]))
# ---- chorus 2 (fragile)
S('L41-0.3', 'night', [I('crescent', 820, 330, s=0.55), I('frost', 540, 1500), I('sword', 540, 1250, s=0.6, anim='tremble', amp=0.8)],
  [F('snow', at='L41', n=60), F('wind', at='L42', n=4)])
S('L43-0.3', 'night', [I('stars', 540, 600, n=18, anim='flicker'), I('moon', 160, 380, s=0.55, to=[900, 330], move=['L43', 'L44.end'], ease=False),
                       I('bandage', 470, 1250, s=1.3, how='draw'), I('candle', 870, 1300, s=0.8)],
  [F('fire', at='L43-0.3', x=870, y=1220, s=0.28), F('tears', at='L44', x=470, y=1330)])
S('L45-0.3', 'storm', [I('darkcloud', 540, 330, s=1.3), I('ground', 540, 1500, col=(90, 110, 90)), I('sword', 540, 1250, s=0.6)],
  [F('bolt', at='L45.5', x=880, y=500, s=0.35), F('wind', at='L45', n=4)])
S('L46-0.3', 'indoor', [I('whetstone', 540, 1250, s=1.3), I('sword', 540, 1130, s=1.0, rot=90, anim='saw', amp=0.9)],
  [F('sparks', at='L46.2', x=540, y=1180, s=0.8)])
S('L47-0.3', 'dark', [I('sword', 540, 950, s=1.2, anim='shake', amp=0.5), I('knot', 540, 1320, s=0.6), I('knot', 540, 1230, s=0.5)],
  [F('embers', at='L47', x=540, y=1500, w=400, h=1200, n=30), F('glow', at='L48', x=540, y=500, r=180, col=(255, 200, 90), z=0)], cam=dict(z=[1.0, 1.14]))
# ---- verse 5
S('L49-1.0', 'dawn', [I('mountains', 540, 650, s=1.0), I('sun', 850, 380, s=0.6), I('path', 540, 1250, s=1.0)],
  [F('footprints', at='L49', end='L49.end+0.5', path=[[600, 1600], [560, 1300], [480, 1050], [520, 900]], n=12, col=(120, 90, 60))])
S('L50-0.3', 'day', [I('ground', 540, 1450), I('stick', 480, 1170, s=0.6, rot=60), I('stick', 600, 1170, s=0.6, rot=-60)] +
  [I('footprint', 540 + 360 * __import__('math').cos(a), 1130 + 250 * __import__('math').sin(a), s=0.2, rot=a * 57.3 + 90, how='fade', dur=0.2,
     **{'in': f'L50+{k * 0.25:.2f}'}) for k, a in enumerate([3.4 + 0.45 * j for j in range(9)])],
  [F('fire', at='L50-0.3', x=540, y=1150, s=0.9), F('embers', at='L50', x=540, y=1100, w=100, h=500, n=12)])
S('L51-0.3', 'night', [I('lantern', 540, 640, s=1.8, anim='swing', amp=0.3),
                       I('shadow', 300, 1250, s=0.8, to=[-150, 1300], move=['L51.3', 'L51.end']),
                       I('shadow', 780, 1250, s=0.8, flip=True, to=[1230, 1300], move=['L51.3', 'L51.end'])],
  [F('glow', at='L51', x=540, y=700, r=520, col=(255, 210, 110), z='back'), F('rays', at='L51.3', x=540, y=700, r0=180, r1=260, z='back')])
S('L52-0.3', 'dusk', [I('sun', 540, 700, s=1.1, to=[540, 1150], move=['L52-0.3', 'L52.end']),
                      I('pine', 130, 1250, col=(40, 70, 60)), I('pine', 330, 1330, s=0.85), I('pine', 540, 1280), I('pine', 750, 1330, s=0.85), I('pine', 950, 1250)],
  [F('eyes', at='L52.3', n=6, gap=0.2, x0=120, x1=960, y0=1200, y1=1450, z=6)])
S('L53-0.3', 'indoor', [I('book', 540, 1000, s=1.15, torn=True, how='fade'), I('candle', 900, 1400, s=0.8)],
  [F('fire', at='L53-0.3', x=900, y=1320, s=0.28), F('pages', at='L53.2', x=400, y=1000, n=4)])
S('L54-0.3', 'indoor', [I('book', 540, 950, s=1.2, tricks=True, how='draw')],
  [F('glow', at='L54.4', x=540, y=950, r=560, col=(255, 230, 150), z='back'), F('sparks', at='L54.5', x=540, y=700, s=1.2)], cam=dict(z=[1.0, 1.1]))
S('L55-0.3', 'night', [I('crystals', 540, 1350, s=1.3, how='pop', **{'in': 'L55.4'})],
  [F('bolt', at='L55.7', x=540, y=820, s=0.8), F('fireworks', at='L55.7'), F('sparks', at='L55.5', x=540, y=1250, s=1.2)])
S('L56-0.3', 'night', [I('tree', 540, 450, s=1.0, bare=True, col=(90, 70, 60)),
                       I('sword', 540, 1100, s=0.85, rot=90, anim='sway', amp=2.5, how='fade', **{'in': 'L56.3'})],
  [F('thread', at='L56.4', path=[[560, 330], [545, 1100]], grow=0.8, w=3, col=(230, 230, 240))])
# ---- breakdown
S('L57-0.3', 'night', [I('tree', 540, 450, s=1.0, bare=True),
                       I('sword', 540, 1100, s=0.85, rot=90, to=[520, 1480], rot_to=70, move=['L57.4', 'L57.4+0.5'], ease=False)],
  [F('thread', at='L57-0.3', end='L57.4', path=[[560, 330], [545, 1100]], grow=0.1, w=3, col=(230, 230, 240)),
   F('smoke', at='L57.4+0.5', end='L57.end+0.5', x=520, y=1520, n=4, s=0.6, h=150, col=(150, 130, 110))])
S('L58-0.3', 'dusk', [I('ground', 540, 1480), I('sword', 540, 1430, s=0.8, rot=84, how='drop', **{'in': 'L58.3'})],
  [F('smoke', at='L58.4', x=540, y=1480, n=5, s=0.8, h=200, col=(160, 130, 100)), F('leaves', at='L58', n=8)], cam=dict(z=[1.05, 1.15], y=[0, 250]))
S('L59-0.3', 'dusk', [I('hill', 540, 1450), I('xiangyun', 540, 520, s=1.0, how='fade', out='L59.4', odur=1.2)],
  [F('birds', at='L59.5', x=300, y=800, n=1), F('wind', at='L59.3', n=3)])
S('L60-0.3', 'dusk', [I('ground', 540, 1480), I('book', 540, 1350, s=0.7, torn=True)],
  [F('pages', at='L60', x=450, y=1300, n=6), F('wind', at='L60', n=6), F('leaves', at='L60', n=10)])
S('L61-0.3', 'dark', [I('stars', 540, 600, n=10, anim='flicker'), I('altar', 540, 1340, s=1.0, broken=True),
                      I('palace', 540, 500, s=0.8, a=0.45, how='fade', out='L62.3', odur=1.5)],
  [F('smoke', at='L61.5', x=540, y=1200, n=3, s=0.5, h=500)])
S('L63-0.3', 'night', [I('village', 540, 1330, lit=True, how='fade')],
  [F('lanterns', at='L63', n=10, gap=0.25, y=1250, rise=5.0)])
S('L64-0.3', 'night', [I('ground', 540, 1500, col=(80, 100, 110)), I('bowl', 540, 1300, s=1.3, rice=False, chopsticks=False), I('sword', 880, 1300, s=0.5, rot=15)],
  [F('rain', at='L64', n=90)], cam=dict(z=[1.0, 1.12]))
# ---- bridge quiet
S('L65-0.5', 'dusk', [I('sun', 850, 700, s=0.7, to=[850, 900], move=['L65', 'L65.end']), I('ground', 540, 1480),
                      I('robe', 300, 1150, s=0.7, a=0.9), I('bundle', 620, 1150, s=1.1, how='pop', **{'in': 'L65.4'})])
S('L66-0.3', 'dusk', [I('mountains', 540, 700, col=(130, 110, 150)), I('path', 540, 1250),
                      I('bundle', 600, 1480, s=0.45, to=[520, 950], move=['L66', 'L66.end+0.5'])],
  [F('footprints', at='L66', end='L66.end', path=[[620, 1600], [560, 1300], [520, 1000]], n=9, col=(120, 90, 60))])
S('L67-0.3', 'dusk', [I('bridge', 540, 650, s=0.9), I('cart', 280, 1330, s=0.9, how='slide_l'),
                      I('basket', 640, 1420, how='pop', **{'in': 'L67.3'}), I('basket', 850, 1380, s=0.85, how='pop', **{'in': 'L67.5'}),
                      I('lantern', 160, 1020, s=0.7, anim='swing'), I('lantern', 700, 1080, s=0.6, anim='swing'),
                      I('bundle', 920, 1150, s=0.5, how='pop', **{'in': 'L67.6'})])
S('L68-0.3', 'dusk', [I('abyss', 700, 1300, s=1.0), I('cliff_l', 130, 1200, s=0.9), I('bridge', 740, 900, s=0.9),
                      I('cart', 200, 780, s=0.6), I('basket', 300, 850, s=0.5), I('lantern', 120, 620, s=0.5, anim='swing')],
  [F('smoke', at='L68', x=900, y=1000, n=4, s=1.3, h=400, col=(120, 110, 140)), F('eyes', at='L68.4', n=3, x0=880, x1=1000, y0=700, y1=900)])
S('L69-0.3', 'dusk', [I('stick', 540, 1250, s=1.2), I('pinwheel', 540, 1030, s=1.4, anim='spin', amp=0.25), I('shoes', 540, 1480, s=0.8)],
  [F('wind', at='L69.3', n=3)])
S('L70-0.3', 'dusk', [I('cloth', 540, 1150, s=1.5), I('bread', 540, 1060, s=1.6, how='rise', **{'in': 'L70.4'})],
  [F('steam', at='L70.5', x=540, y=920, s=1.5), F('glow', at='L70.4', x=540, y=1060, r=480, col=(255, 200, 120), z='back')], cam=dict(z=[1.0, 1.1]))
# ---- build
S('L71-0.3', 'dusk', [I('sun', 540, 500, s=0.9), I('abyss', 540, 1000, s=1.0), I('bridge', 540, 700, s=1.0),
                      I('ground', 540, 1490), I('sword', 540, 1200, s=0.95, how='grow', **{'in': 'L71.3'})])
S('L72-0.3', 'dusk', [I('robe', 540, 950, s=1.4, anim='sway', amp=1.5)], [F('wind', at='L72', n=8), F('leaves', at='L72', n=14)])
S('L73-0.3', 'dusk', [I('cloth', 540, 1150, s=1.4), I('bread', 540, 1060, s=1.5, out='L73.4', odur=0.1),
                      I('bread', 540, 1060, s=1.5, bite=True, how='fade', dur=0.1, **{'in': 'L73.4'}, out='L73.end', odur=0.5)])
S('L74-0.3', 'night', [I('pouch', 540, 1080, s=1.4, anim='shake', amp=0.4)],
  [F('sparks', at='L74.3', x=590, y=700, s=1.2), F('fire', at='L74.7', x=590, y=720, s=0.5), F('glow', at='L74.3', x=540, y=900, r=500, col=(255, 150, 60), z='back')],
  cam=dict(z=[1.0, 1.14]))
# ---- crescendo
S('L75-0.3', 'dark', [I('darkcloud', 300, 250, s=1.2, to=[-200, 250], move=['L75.2', 'L75.end']),
                      I('darkcloud', 800, 280, s=1.2, seed=7, to=[1300, 280], move=['L75.2', 'L75.end']), I('peak', 540, 1400, col=(60, 60, 75))],
  [F('wind', at='L75', n=6)])
S('L76-0.3', 'fire', [I('abyss', 540, 900, s=1.0), I('bridge', 540, 650, s=1.0), I('ground', 540, 1500, col=(90, 70, 60)),
                      I('sword', 540, 1180, s=1.15, how='grow', **{'in': 'L76.2'})],
  [F('eyes', at='L76', n=8, gap=0.15, x0=120, x1=960, y0=200, y1=520), F('rays', at='L76.6', x=540, y=750, r0=150, r1=300, z=3, col=(255, 200, 90))])
# ---- chorus 3 (tragic)
S('L77-0.3', 'fire', [I('abyss', 540, 1000, s=1.0), I('bridge', 540, 700, s=1.0), I('sword', 540, 1150, s=1.0)],
  [F('fire', at='L77.2', x=540, y=1480, s=1.1, z=2), F('embers', at='L77', x=540, y=1500, w=500, h=1300, n=40)])
S('L79-0.3', 'dusk', [I('ground', 540, 1480, col=(120, 100, 80)), I('sword', 330, 1000, s=0.95), I('robe', 740, 1000, s=1.0, blood=True, anim='sway')],
  [F('embers', at='L79', x=540, y=1500, w=500, h=1300, n=20), F('wind', at='L79', n=4)])
S('L80-0.3', 'night', [I('village', 540, 1100, s=1.25, lit=True, how='fade')],
  [F('fireflies', at='L80', n=10, x0=150, x1=930, y0=300, y1=700)])
S('L81-0.3', 'storm', [I('darkcloud', 540, 330, s=1.6), I('peak', 540, 1420), I('sword', 540, 1080, s=1.0)],
  [F('sparks', at='L81.4', end='L81.4+0.3', x=540, y=640, s=0.4), F('wind', at='L81', n=5)])
S('L82-0.3', 'dusk', [I('ground', 540, 1490), I('tree', 540, 450, s=1.0, bare=True), I('sword', 540, 1440, s=0.8, rot=84)],
  [F('thread', at='L82-0.3', path=[[560, 330], [555, 800], [590, 820]], grow=0.1, w=3, col=(230, 230, 240))])
S('L83-0.3', 'night', [I('abyss', 540, 1100, s=1.0), I('cliff_l', 130, 1150, s=0.9), I('cliff_r', 950, 1150, s=0.9), I('bridge', 540, 830),
                       I('lantern', 120, 850, s=0.45, anim='swing', to=[1000, 850], move=['L83', 'L83.end+1'], ease=False),
                       I('lantern', 0, 870, s=0.45, anim='swing', to=[880, 870], move=['L83.2', 'L83.end+1'], ease=False),
                       I('lantern', -120, 850, s=0.45, anim='swing', to=[760, 850], move=['L83.4', 'L83.end+1'], ease=False)])
S('L84-0.3', 'indoor', [I('table', 540, 1360), I('bowl', 540, 1150, s=1.1), I('candle', 870, 1100, s=0.8)],
  [F('smoke', at='L84.4', x=870, y=950, n=3, s=0.4, h=300), F('steam', at='L84', x=540, y=1070, s=0.9)])
# ---- final chorus
S('L85-1.2', 'fire', [I('abyss', 540, 1100, s=1.0), I('bridge', 540, 800, s=1.0, burning=True, how='fade'),
                      I('sword', 540, 900, s=0.9, anim='shake', amp=0.6)],
  [F('boom', at='L85.1', x=540, y=700, s=1.3), F('rays', at='L85.1', x=540, y=650, r0=200, r1=420, z='back', col=(255, 200, 80)),
   F('embers', at='L85', x=540, y=1500, w=500, h=1400, n=50)])
S('L86-0.3', 'fire', [I('monster', 540, 700, s=1.05, how='fade', dur=0.4), I('firewall', 540, 1360, s=1.0, how='rise')],
  [F('embers', at='L86', x=540, y=1500, w=500, h=1400, n=50), F('shake', at='L86.1', amp=1.2, hits=['L86.3'])])
S('L87-0.3', 'fire', [I('pouch', 540, 1000, s=1.2, out='L87.2', odur=0.1)],
  [F('boom', at='L87.2', x=540, y=950, s=1.6, hits=['L87.4']), F('fireworks', at='L87.2', hits='chars:L87'),
   F('embers', at='L87', x=540, y=1500, w=500, h=1400, n=60)])
S('L88-0.3', 'fire', [I('monster', 540, 650, s=0.9, to=[540, 1500], move=['L88.2', 'L88.end+0.4']),
                      I('bridge', 540, 950, s=1.0, burning=True, to=[540, 1300], rot_to=12, move=['L88.2', 'L88.end']),
                      I('sword', 540, 1000, s=1.1, how='rise', **{'in': 'L88.1'}, anim='shake', amp=0.5)],
  [F('boom', at='L88.1', x=540, y=900, s=1.2, hits=['L88.3']), F('rays', at='L88.2', x=540, y=700, r0=180, r1=420, z='back', col=(255, 210, 90)), F('firewall', at='L88') if False else F('embers', at='L88', x=540, y=1500, w=500, h=1400, n=60)])
S('L88.end+0.4', 'dawn', [I('cliff_l', 170, 1150), I('cliff_r', 910, 1150), I('abyss', 540, 1330, s=1.0, a=0.8)],
  [F('smoke', at='L88.end+0.4', x=540, y=1400, n=7, s=1.5, h=1000, col=(160, 150, 150)), F('embers', at='L88.end+0.4', x=540, y=1400, w=300, h=900, n=12)])
# ---- outro
S('L89-0.3', 'dawn', [I('village', 540, 1100, s=0.6, a=0.8), I('ground', 540, 1490), I('stele', 540, 1150, s=0.95, how='grow', dur=1.5)])
S('L90-0.3', 'dawn', [I('stele', 540, 820, s=1.2), I('bowl', 540, 1400, s=1.0, how='pop', **{'in': 'L90.3'})],
  [F('steam', at='L90.4', x=540, y=1310, s=0.9)])
S('L91-0.3', 'day', [I('lantern', 180, 330, s=0.7, anim='swing'), I('lantern', 900, 330, s=0.7, anim='swing'), I('stele', 540, 1030, s=1.1),
                     I('incense', 300, 1440, s=0.9), I('incense', 780, 1440, s=0.9)],
  [F('rays', at='L91.3', x=540, y=700, r0=250, r1=250, z='back'), F('smoke', at='L91', x=300, y=1330, n=3, s=0.4, h=500), F('smoke', at='L91', x=780, y=1330, n=3, s=0.4, h=500)])
S('L92-0.3', 'dawn', [I('sun', 850, 350, s=0.55, col=(240, 200, 170)), I('stele', 540, 1030, s=1.1), I('frost', 540, 1500, how='grow')],
  [F('snow', at='L92', n=50)])
S('L93-0.3', 'dusk', [I('mountains', 540, 1100, col=(150, 140, 170), near=(130, 150, 130)), I('peak', 540, 1420),
                      I('sword', 540, 1090, s=0.8), I('chime', 620, 830, s=0.55, anim='swing', amp=1.5)],
  [F('wind', at='L93', n=6), F('leaves', at='L93', n=8)])
S('L94-0.3', 'night', [I('moon', 800, 300, s=0.8, to=[860, 900], move=['L94-0.3', 'L94.end+0.8']),
                       I('abyss', 700, 1200, s=1.0), I('cliff_l', 150, 1150), I('frost', 540, 1560),
                       I('robe', 300, 820, s=0.55, a=0.9)],
  [F('snow', at='L94', n=30)])
S('L95-0.3', 'dawn', [I('path', 540, 1250), I('signpost', 540, 1050, s=1.0)],
  [F('smoke', at='L95', x=540, y=900, n=6, s=2.0, h=500, col=(235, 230, 235)),
   F('footprints', at='L95', end='L95.end', path=[[560, 1600], [540, 1300], [520, 1050]], n=8, col=(120, 90, 60), a=0.5)])
S('L96-0.3', 'dawn', [I('sun', 540, 700, s=1.0, how='rise'), I('village', 540, 1300, lit=False), I('grass', 250, 1560), I('grass', 850, 1560)],
  [F('smoke', at='L96', x=236, y=1030, n=4, s=0.35, h=600), F('smoke', at='L96.2', x=446, y=980, n=4, s=0.35, h=600),
   F('smoke', at='L96.4', x=656, y=1040, n=4, s=0.35, h=600), F('smoke', at='L96.6', x=876, y=970, n=4, s=0.35, h=600),
   F('birds', at='L96.end', x=540, y=800, n=5)], cam=dict(z=[1.0, 1.1]))

out = sys.argv[1]
old = json.load(open(out, encoding='utf-8'))
ev = [e for e in old.get('events', []) if e['type'] == 'lyricfx']
json.dump(dict(shots=SH, events=ev), open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(SH), 'shots')
