import configparser
import re

import click
import fabric

from .utils import construct_table


@click.group()
@click.pass_context
def cli(ctx):
    """Tools aimed at making work in the Sinzlab easier."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    hosts = config['DEFAULT']['hosts'].split()
    common = config['DEFAULT']['common']
    ctx.ensure_object(dict)
    ctx.obj['hosts'] = ['.'.join([h, common]) for h in hosts]
    ctx.obj['user'] = config['DEFAULT']['user']


@cli.command()
@click.pass_context
def check_gpus(ctx):
    """Get monitoring information for GPUs."""
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
    field_names = (
        'INDEX',
        'UTIL (%)',
        'TEMP (°C)',
        'USED (MiB)',
        'TOTAL (MiB)'
    )
    results = fabric.ThreadingGroup(
        *ctx.obj['hosts'], user=ctx.obj['user']).run(command, hide=True)
    data = {}
    for connection, result in sorted(results.items()):
        result = [l.split(', ') for l in result.stdout.split('\n')][:-1]
        gpus = []
        for line in result:
            gpus.append({k: v for k, v in zip(field_names, line)})
        data[connection] = gpus
    click.echo(construct_table(field_names, data))


@cli.group()
@click.pass_context
def docker(_):
    """Docker commands."""
    pass


@docker.command()
@click.pass_context
def ps(ctx):
    """List running containers."""
    # Find all containers running on all GPU machines and get their ids
    field_names = [
        'ID',
        'Image',
        'Command',
        'RunningFor',
        'Status',
        'Ports',
        'Names',
    ]
    go_template = ', '.join(['{{.' + k + '}}' for k in field_names])
    group = fabric.ThreadingGroup(*ctx.obj['hosts'], user=ctx.obj['user'])
    results = group.run(f'docker ps --format "{go_template}"', hide=True)
    data = {}
    for connection, result in results.items():
        lines = result.stdout.split('\n')[:-1]
        if lines:
            containers = []
            for line in lines:
                values = line.split(', ')
                con_id = values[0]
                container = {k: v for k, v in zip(field_names, values)}
                result = connection.run(
                    'docker inspect --format "{{.Config.Env}}" ' + con_id,
                    hide=True
                )
                match = re.search(
                    r'NVIDIA_VISIBLE_DEVICES=(all|\d+)', result.stdout)
                container['GPU'] = match.group(1) if match else ''
                containers.append(container)
        else:
            containers = []
        data[connection] = containers
    click.echo(construct_table(field_names + ['GPU'], data))


if __name__ == '__main__':
    cli()
