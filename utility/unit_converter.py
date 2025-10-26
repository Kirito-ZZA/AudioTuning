import re
import numpy as np


prefixs = ('yzafpnum kMGTPEZY')

def unit_converter(number, unit):
    if unit == '':
        return number, unit

    unit = unit.strip()

    match = re.search(r"^[a]", unit)
    if match:
        return number * 1E-18, unit[1:]

    match = re.search(r"^[f]", unit)
    if match:
        return number * 1E-15, unit[1:]

    match = re.search(r"^(?:ppm)", unit)
    if match:
        return number * 1E-4, '%'

    match = re.search(r"^[p]", unit)
    if match:
        return number * 1E-12, unit[1:]

    match = re.search(r"^[n]", unit)
    if match:
        return number * 1E-9, unit[1:]

    match = re.search(r"^[u]", unit)
    if match:
        return number * 1E-6, unit[1:]

    match = re.search(r"^[m]", unit)
    if match:
        return number * 1E-3, unit[1:]

    match = re.search(r"^[k]", unit)
    if match:
        return number * 1E3, unit[1:]

    match = re.search(r"^[M]", unit)
    if match:
        return number * 1E6, unit[1:]

    match = re.search(r"^[G]", unit)
    if match:
        return number * 1E9, unit[1:]
    
    match = re.search(r"^[T]", unit)
    if match:
        return number * 1E12, unit[1:]
    
    match = re.search(r"^[P]", unit)
    if match:
        return number * 1E15, unit[1:]

    match = re.search(r"^[E]", unit)
    if match:
        return number * 1E18, unit[1:]

    match = re.search(r"^[Z]", unit)
    if match:
        return number * 1E21, unit[1:]

    match = re.search(r"^[Y]", unit)
    if match:
        return number * 1E24, unit[1:]

    return number, unit

def unit_split(value):
    if isinstance(value, str):
        value = value.strip()
        match = re.search(r"[0-9eE.\-\+]+", value, re.IGNORECASE)
        if match:
            number, unit = float(match.group(0)), value[len(match.group(0)):]
            return unit_converter(number, unit)
    return None, None

def unit_split_raw(value):
    if isinstance(value, str):
        value = value.strip()
        match = re.search(r"[0-9eE.\-\+]+", value, re.IGNORECASE)
        if match:
            number, unit = float(match.group(0)), value[len(match.group(0)):]
            return number, unit
    return None, None

np_log_1000 = np.log(1000)

def format_value(v, u, bits=6):
    try:
        x = bits - int(np.floor( np.log10(abs(v)) ) ) - 1
    except:
        x = -1
    return f"{v:.{x}f} {u}" if x>=0 else f"{v:.{bits-1}e}{u}"

def unit_format(number, unit):
    try:
        n, u = unit_converter(number, unit)
        if abs(n) < 1E-18:
            return 0, u
        x = int(np.floor( np.log(abs(n)) / np_log_1000 ))
        x = x if (8+x)>=0 else -8
        x = x if (8+x)<len(prefixs) else len(prefixs)-8-1
        v, u = n * (0.001**x), "{}{}".format(prefixs[8+x], u)
        return v, u
    except:
        return number, unit

def unit_remove(row, name):
    '''dataFrame单位去除(转成国际标准单位)'''
    if isinstance(row[name], str):
        v, _ = unit_split(row[name])
    else:
        v = row[name]
    return v

if __name__ == "__main__":
    print(unit_split('100mV'))
    print(unit_split_raw('100mV'))
    print(unit_format(1.26, "V"))
    print(unit_format(0.0399, "V"))
    print(unit_format(0.001, "V"))
    print(unit_format(1.23, "V"))
    print(unit_format(100.23, "V"))
    print(unit_format(1000.23, "V"))
    print(unit_format(23250000.0, "V"))