import os
import configparser

import click
import fabric


@click.group()
@click.pass_context
def cli(ctx):
    config = configparser.ConfigParser()
    config.read('config.ini')
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['user'] = os.environ['USER']
    ctx.obj['password'] = os.environ['PASS']


@cli.command()
@click.pass_context
def check_gpus(ctx):
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
                max(len(h) for h in ctx.obj['config']['HOSTS']) + 2)
        else:
            col_widths.append(len(name) + 2)
    width = sum(col_widths) + len(names) - 3
    divider = '+'.join(['-' * w for w in col_widths])
    lines = [
        divider,
        '|'.join([n.center(w) for n, w in zip(names, col_widths)]),
        '|'.join(['', '=' * width, ''])
    ]
    for name, host in ctx.obj['config']['HOSTS'].items():
        c = fabric.Connection(
            host,
            user=ctx.obj['user'],
            connect_kwargs={'password': ctx.obj['password']}
        )
        result = c.run(command, hide=True)
        result = [l.split(', ') for l in result.stdout.split('\n')][:-1]
        for i, line in enumerate(result):
            line = ['', name.upper() if i == 0 else ''] + line + ['']
            line = '|'.join([e.center(w) for e, w in zip(line, col_widths)])
            lines.append(line)
        lines.append(divider)
    output = '\n'.join(lines)
    click.echo(output)


if __name__ == '__main__':
    cli()
