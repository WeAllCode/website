# -*- coding: utf-8 -*-

import arrow


def str_to_bool(s):
    TRUE = ['true', 't', '1', 'yes', 'y']
    FALSE = ['false', 'f', '0', 'no', 'n']

    if s.lower() in TRUE:
        return True
    elif s.lower() in FALSE:
        return False
    else:
        # evil ValueError that doesn't
        # tell you what the wrong value was
        raise ValueError


def local_to_utc(date):
    return arrow.get(date).replace(tzinfo='America/Chicago').to('UTC')
