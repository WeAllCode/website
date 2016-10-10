# -*- coding: utf-8 -*-

import arrow

def str_to_bool(s):
    if s.lower() in ['true', 't', '1', 'yes', 'y']:
        return True
    elif s.lower() in ['false', 'f', '0', 'no', 'n']:
        return False
    else:
        # evil ValueError that doesn't tell you what the wrong value was
        raise ValueError

def local_to_utc(date):
    return arrow.get(date).replace(tzinfo='America/Chicago').to('UTC')
