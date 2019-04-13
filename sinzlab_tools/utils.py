from itertools import zip_longest

import click


def get_host_name(host):
    return host.split('.')[0].upper()


def construct_table(field_names, data):
    # Convert data into something that is easier to construct a table from
    rows = [['HOST', *field_names]]
    for connection, containers in sorted(data.items()):
        host_name = get_host_name(connection.host)
        if not containers:
            rows.append([host_name] + [''] * len(field_names))
        for i, container in enumerate(containers):
            if i == 0:
                row = [host_name]
            else:
                row = [None]
            rows.append(row + list(container.values()))
    # Construct table
    rows = [[''] + row + [''] for row in rows]
    widths = [max(len(x) if x else 0 for x in col) for col in zip(*rows)]
    widths = [w + 2 if w != 0 else w for w in widths]
    div = '+'.join('-' * w for w in widths)
    lines = [div]
    for i, (row1, row2) in enumerate(zip_longest(rows, rows[1:])):
        line = []
        for value, width in zip(row1, widths):
            if value is None:
                value = ''
            line.append(value.center(width))
        lines.append('|'.join(line))
        if i == 0:
            lines.append('|' + '=' * (sum(widths) + len(row1) - 3) + '|')
        else:
            if row2:
                no_div = [True if x is None else False for x in row2]
            else:
                no_div = [False] * len(row1)
            div = ''
            last_column_was_empty = False
            for is_empty, width in zip(no_div, widths):
                if width == 0:
                    continue
                if is_empty:
                    div += '|' + ' ' * width
                    last_column_was_empty = True
                else:
                    if last_column_was_empty:
                        div += '|'
                        last_column_was_empty = False
                    else:
                        div += '+'
                    div += '-' * width
            lines.append(div + '+')
    return '\n'.join(lines)
