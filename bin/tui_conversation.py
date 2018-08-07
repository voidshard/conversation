import argparse
import os
import sys
import random

from conversation.handlers import InMemoryHandler
from conversation.backend import FilesystemStorage
from conversation.domain import models


_QUIT = ["q", "quit", "exit"]


def parse_args():
    loc = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")

    a = argparse.ArgumentParser()
    a.add_argument("-l", "--location", default=loc, help=f"Defaults to {loc}")
    a.add_argument("-n", "--name", help="conversation file to load")

    return a.parse_args()


def read_input(options) -> int:
    ans = None

    while ans is None:
        i = input("> ")

        if i in _QUIT:
            sys.exit(0)

        try:
            ans = int(i)
        except:
            pass

        if ans not in options:
            ans = None

    return ans


def send_message(state: dict, node: models.Node, replies: list) -> models.Node:
    print(node.text.format(**state))

    if not replies:
        exit(0)

    ids = {}
    for r in replies:
        print("%s) " % len(ids), r.text.format(**state))
        ids[len(ids)] = r

    i = read_input(ids.keys())
    return ids[i]


def run_conversation(handler):
    nxt = send_message(handler.state(), handler.current_node, handler.next_nodes())

    while nxt:
        handler.current_node = nxt

        if nxt.Type.Reply == nxt.type:
            options = handler.next_nodes()
            if not options:
                exit(0)

            next_message = random.choice(options)
            handler.current_node = next_message

        nxt = send_message(handler.state(), handler.current_node, handler.next_nodes())


def main(args):
    fs = FilesystemStorage()

    if not args.name:
        for i in fs.list(args.location):
            print(i)
        return

    graph = fs.read(args.name, args.location)
    hnd = InMemoryHandler(graph)
    run_conversation(hnd)


if __name__ == "__main__":
    args = parse_args()
    main(args)
