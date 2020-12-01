#!/usr/bin/env python3

import argparse
import re
import sys
from collections import OrderedDict
from itertools import groupby

class Map(OrderedDict):
    def __init__(self, files):
        super().__init__()
        self.process = {}
        for fn in files:
            f = open(fn, 'r')
            for line in f:
                line = line.strip()
                if not line or line.startswith('//') or line.startswith('#'):
                    continue
                parts = line.split(':')
                if len(parts) > 2:
                    print("ERROR: Line %s has multiple ':'" % line)
                    sys.exit(1)
                k, v = [x.strip() for x in parts]
                if k.startswith("@"):
                    self.process[re.compile(k[1:])] = v
                else:
                    self[re.compile(k)] = v

    def search(self, map_v):
        for k, v in self.items():
            if re.search(k, map_v):
                return v
        return None

    def search_process(self, map_v):
        for k, v in self.process.items():
            if re.search(k, map_v):
                return v
        return None


class Script():

    do_addr = False

    def __init__(self, fn):
        self.events = {}
        self.total = 0

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
        match = re.match("(?P<comm>.*)\s+(?P<pid>[0-9]+).*:\s+(?P<cycles>[0-9]+)", symbol)
        if not match:
            raise Exception("Invalid format %s" % symbol)
        s = []
        #Parse the stack
        for line in stack:
            r = re.match("([0-9a-f]+)[ ]+(.+?)([+]0x[0-9a-f]+)?[ ]+\((.+)\)", line)
            if r:
                s.append((r.group(1),r.group(2),r.group(4)) if self.do_addr else ("", r.group(2),r.group(4)))
        pstack = [sp for sp in s if (len(sp) > 1 and sp[1] != '[unknown]' and sp[1] != '??')]
        pstack = [x[0] for x in groupby(pstack)]
        stackref = '\n'.join([' '.join(ls) for ls in pstack]) + match.group('comm')
        self.total += int(match.group('cycles'))
        if stackref in self.events:
            self.events[stackref] = ((self.events[stackref][0][0]+int(match.group('cycles')), self.events[stackref][0][1]),self.events[stackref][1])
        else:
            self.events[stackref] = ((int(match.group('cycles')), match.group('comm')),
             pstack)

    def get_events(self):
        return self.events.values()

def perfclass():
    parser = argparse.ArgumentParser(description='Perf mapper')
    parser.add_argument('script', metavar='script', type=str, nargs=1,
                        help='The perf script')
    parser.add_argument('--map', metavar='map', type=str, nargs='+',
                        help='The perf map', default=[])
    parser.add_argument('--show-match', dest='show_match', action='store_true',
                        default=False,
                        help='Show match')
    parser.add_argument('--show-failed', dest='show_failed', action='store_true',
                        default=False,
                        help='Show failed matching')
    parser.add_argument('--parse-address', dest='do_addr', action='store_true',
                        default=False,
                        help='Parse the address in code')
    parser.add_argument('--cycles', dest='cycles', action='store_true',
                        default=False,
                        help='Print in cycles')
    parser.add_argument('--no-output-failed', dest='output_failed', action='store_false',
                        default=True,
                        help='Output symbols that failed matching')
    parser.add_argument('--min', metavar='min', type=float, nargs='?', default=0,
                        help='Minimum percentage to output')
    parser.add_argument('--separator', metavar='separator', type=str, nargs='?', default=';',
                        help='Separator')
    parser.add_argument('--stack-max', metavar='stack_max', type=int, nargs='?', default=100,
                        help='Maximum number of function to check in the stack')

    args = parser.parse_args()

    script = Script(args.script[0])
    script.do_addr = args.do_addr
    map = Map(args.map)

    matched = 0
    classes = {}
    unknowns = set()
    events = list(script.get_events())
    events.sort(key=lambda x:x[0][0])
    for (cycles, process), stack in reversed(events):
        found = False

        for i, (addr, symbol, location) in enumerate(stack):
            if i >= args.stack_max:
                break
            if location == '([kernel.kallsyms])':
                symbol = 'k'+symbol
            c = map.search(symbol)
            if c:
                found = True
                break

        if not found:
            c = map.search_process(process)
            if c:
                found = True
            else:
                if len(stack) == 0:
                    symbol = process
                elif len(stack[0]) == 1:
                    symbol = stack[0][0]
                else:
                    symbol = stack[0][1]
                if not symbol in unknowns:
                    if args.show_failed and cycles * 100 / script.total > args.min:
                        print("Could not find symbol %s (%d cycles) in map, process %s" % (symbol, cycles, process), file=sys.stderr)
                        for addr, subsymbol, whatever in stack:
                            print("\t%s" % subsymbol, file=sys.stderr)
                    unknowns.add(symbol)
                if args.output_failed:
                    classes.setdefault(symbol, 0)
                    classes[symbol] += cycles
                continue
        if found:
            classes.setdefault(c, 0)
            classes[c] += cycles
            matched += cycles
            if args.show_match:
                print("%s -> %s (process %s)" % (symbol, c, process), file=sys.stderr)
                for addr, subsymbol, whatever in stack:
                    print("\t%s" % subsymbol, file=sys.stderr)
            continue

    print("Finished, matched %f%% of cycles in %d events" % (100 * matched / float(script.total), len(events)), file=sys.stderr)
    for name, cycles in sorted(list(classes.items()), key=lambda x: x[1], reverse=True):
        pc = cycles * 100 / float(script.total if args.output_failed else matched)
        if pc > args.min:
            if args.cycles:
                print("%s%s%d" % (name.strip('_'), args.separator, cycles))
            else:
                print("%s%s%f" % (name.strip('_'), args.separator, pc))

if __name__ == "__main__":
    perfclass()
