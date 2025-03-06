def remove_storage_prefix(url: str) -> str:
    """
    Remove the storage prefix (https://storage.googleapis.com) from a URL
    
    Args:
        url: The full URL string
        
    Returns:
        str: URL without the storage prefix
    """
    storage_prefix = "https://storage.googleapis.com/soundful/"
    if url.startswith(storage_prefix):
        return url[len(storage_prefix):]
    return url 


def add_storage_prefix(url: str) -> str:
    """
    Add the storage prefix (https://storage.googleapis.com) to a URL
    
    Args:
        url: The full URL string
    """ 
    return f"https://storage.googleapis.com/soundful/{url}"