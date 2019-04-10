import configparser

import click
import fabric


@click.group()
@click.pass_context
def cli(ctx):
    config = configparser.ConfigParser()
    config.read('config.ini')
    hosts = config['DEFAULT']['hosts'].split()
    ext = config['DEFAULT']['institution']
    ctx.ensure_object(dict)
    ctx.obj['hosts'] = {'.'.join([host, ext]): host.upper() for host in hosts}
    ctx.obj['user'] = config['DEFAULT']['user']


@cli.command()
@click.pass_context
def check(ctx):
    """Check all GPUs."""
    command = (
        'nvidia-smi '
        + '--format=csv,noheader,nounits '
        + '--query-gpu=' + (
            'index,'
            + 'utilization.gpu,'
            + 'temperature.gpu,'
            + 'memory.used,'
            + 'memory.total'
        )
    )
    names = (
        '',
        'HOST',
        'INDEX',
        'UTIL (%)',
        'TEMP (°C)',
        'USED (MiB)',
        'TOTAL (MiB)',
        ''
    )
    col_widths = []
    for name in names:
        if name == '':
            col_widths.append(0)
        elif name == 'HOST':
            col_widths.append(
                max(len(h) for h in ctx.obj['hosts'].values()) + 2)
        else:
            col_widths.append(len(name) + 2)
    width = sum(col_widths) + len(names) - 3
    divider = '+'.join(['-' * w for w in col_widths])
    lines = [
        divider,
        '|'.join([n.center(w) for n, w in zip(names, col_widths)]),
        '|'.join(['', '=' * width, ''])
    ]
    results = fabric.ThreadingGroup(
        *ctx.obj['hosts'].keys(), user=ctx.obj['user']).run(command, hide=True)
    for connection, result in sorted(results.items()):
        result = [l.split(', ') for l in result.stdout.split('\n')][:-1]
        for i, line in enumerate(result):
            line = [ctx.obj['hosts'][connection.host] if i == 0 else ''] + line
            line = [''] + line + ['']
            line = '|'.join([e.center(w) for e, w in zip(line, col_widths)])
            lines.append(line)
        lines.append(divider)
    output = '\n'.join(lines)
    click.echo(output)


if __name__ == '__main__':
    cli()
