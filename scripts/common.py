# common.py
# Holden Bailey 2026
# Common functions for Seattle Permitting Project

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


if __name__ == '__main__':
    print(base_from_url('https://sub.domain.tld/dir/subdir/file.txt'))