def default_c_presenter(value):
    """
    default_c_presenter(value) -> str

    .. deprecated:: 0.5

    This is the default presenter used by C function tests. Currently it is
    just a dummy as the presenter system is undergoing modifications.
    """


    if isinstance(value, (list, tuple)):
        parts = []
        for val in value:
            if isinstance(val, ffi.CData):
                parts.append(str(val))
                #ctype = cdata_pat.search(str(val)).groupdict()["type"]
                #if "*" in ctype:
                #    parts.append(ctype + "->" + str(val[0]))
                #elif "[" in ctype:
                #    pass #array printing

            else:
                parts.append(str(val))

        return " ".join(parts)

    else:
        if isinstance(value, ffi.CData):
            return value
            #ctype = cdata_pat.search(str(value)).groupdict()["type"]
            #if "*" in ctype:
            #    return ctype + "->" + str(value[0])
            #elif "[" in ctype:
            #    pass
        else:
            return value

def default_c_call_presenter(func_name, args):
    """
    This function is used for showing the way the student function was called
    during a test. It forms a function call code line using the function name
    and its arguments. If the call would be long (over 80 characters), it is
    split to multiple lines.
    """

    call = func_name + "("
    if len(str(args)) > 80:
        call += "\n"
        call += ",\n".join("    " + repr(arg) for arg in args)
        call += "\n)"
    else:
        call += ", ".join(repr(arg) for arg in args)
        call += ");"

    return "{{{highlight=c\n" + call + "\n}}}"

def default_c_value_presenter(value):
    return repr(value)
