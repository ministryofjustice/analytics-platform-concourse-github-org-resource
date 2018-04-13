from contextlib import redirect_stdout
import json
import os
import sys


class Resource(object):

    def __init__(self, fn):
        self.fn = fn

        self.action = os.path.basename(sys.argv[0]).lower()

        self.args = []
        if self.action in ('in', 'out'):
            self.args.append(sys.argv[1])

        self.kwargs = json.loads(sys.stdin.read())

    def __call__(self):
        with redirect_stdout(sys.stderr):
            response = self.fn(*self.args, **self.kwargs)

        print(json.dumps(response))
