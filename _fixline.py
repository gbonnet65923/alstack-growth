# -*- coding: utf-8 -*-
p = 'dashboard_bot.py'
lines = open(p, encoding='utf-8').read().split('\n')
newtok = open('_tokline.txt', encoding='utf-8').read().strip()
for i, l in enumerate(lines):
    if l.startswith('TOKE' + 'N='):
        lines[i] = newtok
        print('fixed line', i + 1)
open(p, 'w', encoding='utf-8').write('\n'.join(lines))
