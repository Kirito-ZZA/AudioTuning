import re
import numpy as np

prefixs = ('yzafpnum kMGTPEZY')


def addSpliter(v):
    '''添加分隔符'''
    v_int, v_dec = v.split('.')
    if v_int[0] in ['+', '-']:
        prefix = v_int[0]
        v_int = v_int.strip(v_int[0])
    else:
        prefix = ''
    int_list, dec_list = list(v_int), list(v_dec)
    int_list.reverse()
    for ls in [int_list, dec_list]:
        i = 3
        while i < len(ls):
            ls.insert(i, ' ')
            i += (3+1)
    int_list.reverse()

    v = prefix + ''.join(int_list) + '.' + ''.join(dec_list)

    return v


def value_format(v, u='', bits=8):
    '''
    格式化字符串/数值显示
    v -> str/float
    u -> str 单位
    bits -> int 总位数
    '''
    v = f'{v:,.{bits}f}'

    v_int, v_dec = v.split('.')
    # 位数处理
    bit = bits + 1 - len(str(v_int)) if str(v_int)[0] in ['+', '-'] else \
        bits - len(str(v_int))
    v_dec = round(float('.' + v_dec), bit)

    v_dec = f'{v_dec:,.{bit}f}'
    v = v_int + v_dec.replace('0.', '.')
    # 添加分隔符
    v = addSpliter(v)

    return v, u


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


def unit_format(number, unit):
    try:
        n, u = unit_converter(number, unit)
        if abs(n) < 1E-15:
            return n, u
        x = int(np.floor(np.log(abs(n)) / np_log_1000))
        x = x if (8+x) >= 0 else -8
        x = x if (8+x) < len(prefixs) else len(prefixs)-8-1
        v, u = n * (0.001**x), "{}{}".format(prefixs[8+x], u)
        return v, u
    except:
        return number, unit


def format_value(v, u='', bits=6):
    try:
        x = bits - int(np.floor(np.log10(abs(v)))) - 1
    except:
        x = -1
    return f"{v:.{x}f} {u}" if x >= 0 else f"{v:.{bits-1}e}{u}"


def bit_format(row, name, bits=8):
    '''df 数值位数处理'''
    if isinstance(row[name], float):
        int_l = len(str(int(row[name])))
        bit = bits - int_l
        v = format_value(row[name], '', bit)
    elif isinstance(row[name], int):
        int_l = len(str(row[name]))
        bit = bits - int_l
        v = format_value(row[name], '', bit)
    else:
        v = row[name]
    return v

if __name__ == '__main__':
    print(value_format(03e-06, bits=9))
    print(unit_converter(50.000235, 'MHz'))
    print(unit_format(50.000000235, 'MHz'))
    print(unit_format(6.156e-7, 'MHz'))
    # print(value_format(1111.4867632))
    # print(value_format(-2222.4867633))
    # print(value_format('-3333.4867634'))
    # print(value_format('4444.4867635'))
    # print(value_format(132.4867632))
