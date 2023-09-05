import os
import cffi
from pysenpai.messages import load_messages, Codes
from pysenpai.output import json_output, output


proto_pat = re.compile("(?:[A-Za-z0-9_]+\s+)+[A-Za-z0-9_]+\s*\((?:[A-Za-z0-9_\* ]+,?)*\)\s*;")
cdata_pat = re.compile("<cdata '(?P<type>[A-Za-z0-9_ \*]+)' owning (?P<bytes>[0-9]+) bytes>")

ffi = cffi.FFI()


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



def load_with_verify(st_c_filename, lang="en", custom_msgs={}, typedefs={}, req_stdio=False):
    lib_name, ext = os.path.splitext(st_c_filename)
    msgs = load_messages(lang, "c_load")
    msgs.update(custom_msgs)

    json_output.new_test(msgs.get_msg("LoadingLibrary", lang)["content"].format(name=st_c_filename))
    json_output.new_run()

    fd_o = sys.stderr.fileno()
    orig_stderr = os.fdopen(os.dup(fd_o), "w")

    save = sys.stderr

    if typedefs:
        for td in typedefs[lang]:
            ffi.cdef(td)

    if os.path.exists(lib_name + ".h"):
        headers = lib_name + ".h"
    else:
        headers = lib_name + ".c"

    try:
        with open(headers, encoding="utf-8-sig") as source:
            contents = source.readlines()
            protos, has_stdio = find_prototypes(contents)

            ffi.cdef("\n".join(protos))
    except UnicodeDecodeError:
        output(msgs.get_msg("EncodingError", lang), ERROR)
        return None


    if req_stdio or has_stdio:
        ffi.cdef("extern FILE* stdout;")
        ffi.cdef("void setbuf(FILE *stream, char *buf);")

    freopen("err", "w", sys.stderr)

    with open(st_c_filename) as source:
        try:
            st_lib = ffi.verify(source.read())
        except:
            os.dup2(orig_stderr.fileno(), sys.stderr.fileno())
            output(msgs.get_msg("CompileError", lang), ERROR)
            with open("err", "r") as f:
                print(f.read())
            return None

    os.dup2(orig_stderr.fileno(), sys.stderr.fileno())

    if req_stdio or has_stdio:
        try:
            st_lib.setbuf(st_lib.stdout, ffi.NULL)
        except AttributeError:
            output(msgs.get_msg("NoStdIO", lang), ERROR)
            return None

    return st_lib


def load_library(st_c_filename, so_name, lang="en", custom_msgs={}, typedefs={}, req_stdio=False):
    """
    load_library(st_c_filename, so_name[, lang="en"][, custom_msgs={}][, typedefs={}][, req_stdio=False]) -> CFFI dynamic library object

    This function loads the student code as a library so that we can later call
    its functions. The loading has two parts: initializing the CFFI dynamic
    library object, and defining the function headers. Both of these are
    hanled by `Link CFFI <http://cffi.readthedocs.io/en/latest/index.html>`_.
    In order to load the library, *so_name* must match the name given to the
    .so (or dll in Windows) when compiling. The argument is given as a
    dictionary with language codes as keys and corresponding so names as
    values.

    In the current implemenation struct definitions and similar are not parsed
    from .c files (but they are parsed from .h files). Instead, if students are
    epxected to use given structs, their definitios should be included in the
    *typedefs* argument. Note that this is only needed for types that need to
    be exposed to the checker - and usually in these situations you should
    already know what they are going to be. E.g. if you need to give pointers
    to structs in the test vector, then the definition of that struct needs to
    be in the *typedefs* dictionary. This dictionary has language codes as its
    keys and definition strings as values. All types should be in one string.

    If the student code is expected to print something that needs to be
    evaluated, then *req_stdio* must be set to True. There is a degree of
    mysticism involved in redirecting C stdio to files and setting the flag to
    True performs that particular sorcery. However, it fails if the student
    code does not include stdio. A message is shown in the output in this case.
    """

    lib_name, ext = os.path.splitext(st_c_filename)
    so_name = so_name.get(lang, so_name["en"])
    msgs = load_messages(lang, "c_load")
    msgs.update(custom_msgs)

    json_output.new_test(msgs.get_msg("LoadingLibrary", lang)["content"].format(name=st_c_filename))
    json_output.new_run()

    if "/" not in lib_name:
        lib_name = "./" + lib_name

    try:
        st_lib = ffi.dlopen("./" + so_name + ".so")
    except:
        etype, evalue, etrace = sys.exc_info()
        ename = evalue.__class__.__name__
        emsg = str(evalue)
        output(msgs.get_msg(ename, lang, default="GenericErrorMsg"), ERROR, ename=ename, emsg=emsg)
        return None

    if typedefs:
        for td in typedefs[lang]:
            ffi.cdef(td)

    if os.path.exists(lib_name + ".h"):
        headers = lib_name + ".h"
    else:
        headers = lib_name + ".c"

    try:
        with open(headers, encoding="utf-8-sig") as source:
            contents = source.readlines()
            protos, has_stdio = find_prototypes(contents)

            ffi.cdef("\n".join(protos))
    except UnicodeDecodeError:
        output(msgs.get_msg("EncodingError", lang), ERROR)
        return None
    except cffi.api.CDefError:
        output(msgs.get_msg("InvalidPrototype", lang), ERROR)
        return None


    # magic workaround; without this stdout redirects in the test_c_function function don't work.
    # the workaround sets the C stdout buffer to NULL which forces it to output everything
    # without buffering.

    if req_stdio or has_stdio:
        try:
            ffi.cdef("extern FILE* stdout;")
            ffi.cdef("void setbuf(FILE *stream, char *buf);")
            st_lib.setbuf(st_lib.stdout, ffi.NULL)
        except AttributeError:
            output(msgs.get_msg("NoStdIO", lang), ERROR)
            return None

    return st_lib
