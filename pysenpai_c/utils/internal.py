import os
import random
import re
import string

proto_pat = re.compile("(?:[A-Za-z0-9_]+\s+)+[A-Za-z0-9_]+\s*\((?:[A-Za-z0-9_\* ]+,?)*\)\s*;")
cdata_pat = re.compile("<cdata '(?P<type>[A-Za-z0-9_ \*]+)' owning (?P<bytes>[0-9]+) bytes>")

def find_prototypes(content):
    """
    find_prototypes(content) -> list

    This function locates function prototypes from a .c file. These are needed
    for defining the functions within CFFI. It's a work in progress and at its
    present stage can sometimes fail to find prototypes even if they are
    there. The function is not used for .h files.
    """


    protos = []
    comment = False
    has_stdio = False
    for line in content:
        #if line.strip().endswith("{") and not line.strip().startswith("struct"):
        #    break
        if line.startswith("//"):
            continue

        line = line.strip()
        if "<stdio.h>" in line:
            has_stdio = True

        if "/*" in line:
            if "*/" not in line:
                comment = True
        if comment and "*/" in line:
            comment = False

        if not comment:
            line = line.split("//")[0].split("/*")[0].strip()
            if line.endswith(";") and not line.startswith("return"):
                if proto_pat.match(line):
                    protos.append(line)
    return protos, has_stdio


def input_to_file(content):
    """
    input_to_file(content) -> str

    This function is used internally to put inputs into a file - the method
    used by the core module (using StringIO) does not change where C code looks
    for its stdin. This function prepares a file that where we can redirect
    stdin for the C code.
    """

    fn = "".join(random.choices(string.ascii_lowercase, k=16))
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

