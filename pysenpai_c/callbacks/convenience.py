def aggressive_rounding_validator(ref, res, out):
    """
    This convenience validator performs more aggressive rounding validation for
    floats than the rounding validator in the core module. It rounds off all
    decimals. This can sometimes be useful if dealing with results with a lot
    of decimals.
    """

    assert round(ref) == round(res)
