def chunk_list(datas, chunksize):
    """Split list into the chucks

    Params:
        datas     (list): data that want to split into the chunk
        chunksize (int) : how much maximum data in each chunks

    Returns:
        chunks (obj): the chunk of list
    """

    for i in range(0, len(datas), chunksize):
        yield datas[i : i + chunksize]
