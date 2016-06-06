# -*- coding: utf-8 -*-

import arrow

def str_to_bool(s):
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        # evil ValueError that doesn't tell you what the wrong value was
        raise ValueError

def local_to_utc(date):
    return arrow.get(date).replace(tzinfo='America/Chicago').to('UTC')
