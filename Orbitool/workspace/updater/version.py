import packaging


def convert_to_tuple(version: str):
    return tuple(map version.split('.'))
