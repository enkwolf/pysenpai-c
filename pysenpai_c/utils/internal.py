

def input_to_file(content):
    """
    input_to_file(content) -> str

    This function is used internally to put inputs into a file - the method
    used by the core module (using StringIO) does not change where C code looks
    for its stdin. This function prepares a file that where we can redirect
    stdin for the C code.
    """

    fn = "".join([random.choice(alnum) for i in range(16)])
    with open(fn, "w") as f:
        f.write(content + "\n")
    return fn


# https://stackoverflow.com/questions/20000332/repeated-redirection-of-low-level-stdin-in-python
def freopen(f, mode, stream):
    """
    This function is used internally to redirect stdin and stdout to files. The
    method used by the core module is not sufficient for testing C code which
    is why we need to manipulate file descriptors through the os module instead.
    """

    oldf = open(f, mode)
    oldfd = oldf.fileno()
    newfd = stream.fileno()
    os.close(newfd)
    os.dup2(oldfd, newfd)

