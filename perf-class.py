#!/bin/env python

import argparse
import re
import sys
from collections import OrderedDict


class Map(OrderedDict):
    def __init__(self, files):
        super().__init__()
        for fn in files:
            f = open(fn, 'r')
            for line in f:
                line = line.strip()
                if not line or line.startswith('//') or line.startswith('#'):
                    continue
                k, v = [x.strip() for x in line.split(':', 1)]
                self[re.compile(k)] = v

    def search(self, map_v):
        for k, v in self.items():
            if re.search(k, map_v):
                return v
        return None


class Script():
    events: dict

    def __init__(self, fn):
        self.events = []

        symbol = None
        stack = []
        f = open(fn, 'r')
        for line in f:

            sline = line.strip()
            if sline == '':
                if symbol:
                    self.__add_symbol(symbol, stack)
                symbol = None
                continue

            if symbol:
                stack.append(sline)
                continue
            else:
                symbol = sline
                stack = []

        if symbol:
            self.__add_symbol(symbol, stack)

    def __add_symbol(self, symbol, stack):
        match = re.match("(?P<comm>.*)\s+(?P<pid>[0-9]+).*:\s+(?P<cycles>[0-9]+)",symbol)
        if not match:
            raise Exception("Invalid format %s" % symbol)

        self.events.append((int(match.group('cycles')), [s.split(' ') for s in stack]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Perf mapper')
    parser.add_argument('script', metavar='script', type=str, nargs=1,
                        help='The perf script')
    parser.add_argument('--map', metavar='map', type=str, nargs='+',
                        help='The perf map')
    parser.add_argument('--show-match', dest='show_match', action='store_true',
                        default=False,
                        help='Show match')
    parser.add_argument('--show-failed', dest='show_failed', action='store_true',
                        default=False,
                        help='Show failed matching')
    parser.add_argument('--no-output-failed', dest='output_failed', action='store_false',
                        default=True,
                        help='Output symbols that failed matching')
    parser.add_argument('--min', metavar='min', type=float, nargs='?', default=0,
                        help='Minimum percentage to output')
    parser.add_argument('--separator', metavar='separator', type=str, nargs='?', default=';',
                        help='Separator')

    args = parser.parse_args()

    script = Script(args.script[0])
    map = Map(args.map)

    total = 0
    matched = 0
    classes = {}
    unknowns = set()
    for cycles, stack in script.events:
        found = False
        for addr,symbol,whatever in stack:
            c = map.search(symbol)
            if c:
                classes.setdefault(c, 0)
                classes[c] += cycles
                total += cycles
                matched += cycles
                found = True
                if args.show_match:
                    print("%s -> %s" % (symbol, c), file=sys.stderr)
                break
        if not found:
            symbol = stack[0][1]
            if not symbol in unknowns:
                if args.show_failed:
                    print("Could not find symbol %s in map" % symbol, file=sys.stderr)
                    for addr, subsymbol, whatever in stack:
                        print("\t%s" % subsymbol, file=sys.stderr)
                unknowns.add(symbol)
            if args.output_failed:
                classes.setdefault(symbol, 0)
                classes[symbol] += cycles
            total += cycles

    print("Finished, matched %f%% of cycles" % (100 * matched / float(total)), file=sys.stderr)
    for name,cycles in sorted(list(classes.items()), key=lambda x: x[1], reverse=True):
        pc = cycles * 100 / float(matched if args.output_failed else total)
        if pc > args.min:
            print("%s%s%f" % (name, args.separator, pc))



