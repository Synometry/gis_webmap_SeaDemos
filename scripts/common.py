# common.py
# Holden Bailey 2026
# Common functions for Seattle Permitting Project

import numpy as np
import pandas as pd

from log import log, register
register('Common Functions')

def base_from_url(url: str) -> str:
    """base_from_url extracts the base address from a url string

    :param url: the url string from which a base is extracted. Assumes the url begins with "https://".
    :type url: str
    :return: the base address prefixing the url provided
    :rtype: str
    
    .. code-block:: python
    
        >>> base_from_url('https://sub.domain.tld/dir/subdir/file.txt')
        https://sub.domain.tld
    """
    
    return '/'.join(url.split('/')[:3])

def survey_data(data: pd.DataFrame) -> None:
    namelist = ['name:']
    typelist = ['type:']
    maxlist = ['maximum:']
    uniquelist = ['unique:']
    for (c, t) in zip(data.columns, data.dtypes):
        namelist.append(c)
        typelist.append(t)
        uniquelist.append(str(data[c].is_unique))
        if isinstance(t, pd.StringDtype):
            maxlist.append(np.max(data[c].str.len()))
        else:
            maxlist.append(np.max(data[c]))
    log(namelist, typelist, maxlist, uniquelist)
    


if __name__ == '__main__':
    print(base_from_url('https://sub.domain.tld/dir/subdir/file.txt'))