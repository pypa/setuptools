cdef extern char *get_hello_msg()

def hello():
    return get_hello_msg()
