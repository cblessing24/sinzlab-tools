import configparser

import click

from sinzlab_tools import exec
from sinzlab_tools.utils import construct_table


@click.group()
@click.option(
    '-h',
    '--hosts',
    type=click.STRING,
    help='Run command on specified hosts (default all).'
)
@click.pass_context
def cli(ctx, hosts):
    """Tools aimed at making work in the Sinzlab easier."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    if hosts:
        hosts = hosts.split(',')
    else:
        hosts = config['DEFAULT']['hosts'].split()
    common = config['DEFAULT']['common']
    ctx.ensure_object(dict)
    ctx.obj['hosts'] = ['.'.join([h, common]) for h in hosts]
    ctx.obj['user'] = config['DEFAULT']['user']


@cli.command()
@click.pass_context
def check_gpus(ctx):
    """Get monitoring information for GPUs."""
    queries = {
        'INDEX': 'index',
        'UTIL (%)': 'utilization.gpu',
        'TEMP (°C)': 'temperature.gpu',
        'USED (MiB)': 'memory.used',
        'TOTAL (MiB)': 'memory.total'
    }
    all_stats = exec.run_nvidia_smi(
        ctx.obj['hosts'], ctx.obj['user'], queries.values())
    data = {}
    for conn, conn_stats in all_stats.items():
        gpus = []
        for gpu_stats in conn_stats:
            gpus.append({k: v for k, v in zip(queries, gpu_stats)})
        data[conn] = gpus
    click.echo(construct_table(queries, data))


@cli.group()
@click.pass_context
def docker(_):
    """Docker commands."""
    pass


@docker.command()
@click.option(
    '-a',
    '--all',
    'all_containers',
    is_flag=True,
    help='Show all containers (default shows just running).'
)
@click.option(
    '-f',
    '--filter',
    'container_filters',
    type=click.STRING,
    multiple=True,
    help='Filter output based on conditions provided.'
)
@click.option(
    '-n',
    '--last',
    'n_last_containers',
    type=click.INT,
    help='Show n last created containers (includes all states) (default -1).'
)
@click.option(
    '-l',
    '--latest',
    'latest_container',
    is_flag=True,
    help='Show the latest created container (includes all states).'
)
@click.pass_context
def ps(
        ctx,
        all_containers,
        container_filters,
        n_last_containers,
        latest_container
):
    """List containers."""
    # Assemble docker ps command
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
    command = [f'docker ps --format "{go_template}"']
    if all_containers:
        command.append('--all')
    for container_filter in container_filters:
        command.append(f'--filter {container_filter}')
    if n_last_containers:
        command.append(f'--last {n_last_containers}')
    if latest_container:
        command.append('--latest')
    command = ' '.join(command)
    # Run command
    outputs = exec.run_group_command(
        ctx.obj['hosts'], ctx.obj['user'], command)
    # Parse results
    data = {}
    for connection, output in outputs.items():
        containers = []
        for line in output:
            if not line:
                continue
            values = line.split(', ')
            container = {k: v for k, v in zip(field_names, values)}
            container['GPU'] = exec.get_container_gpu(connection, values[0])
            containers.append(container)
        data[connection] = containers
    # Print result as table
    click.echo(construct_table(field_names + ['GPU'], data))


@docker.command()
@click.option(
    '-u',
    '--username',
    type=click.STRING,
    prompt=True,
    help='Username.'
)
@click.option(
    '-p',
    '--password',
    type=click.STRING,
    prompt=True,
    hide_input=True,
    help='Password.'
)
@click.pass_context
def login(ctx, username, password):
    """Log in to a Docker registry."""
    command = f'docker login -u {username} -p {password}'
    exec.run_group_command(ctx.obj['hosts'], ctx.obj['user'], command)


@docker.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True
))
@click.argument('image')
@click.pass_context
def pull(ctx, image):
    """Pull an image or a repository from a registry."""
    command = ' '.join([f'docker pull {image}'] + ctx.args)
    exec.run_group_command(ctx.obj['hosts'], ctx.obj['user'], command)


@docker.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True
))
@click.option('--name', 'custom_name', type=click.STRING)
@click.argument('docker_run_args', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def run(ctx, custom_name, docker_run_args):
    """Run a command in a new container."""
    base_command = 'docker run --runtime nvidia'
    # Get indexes of available GPUs
    all_stats = exec.run_nvidia_smi(
        ctx.obj['hosts'], ctx.obj['user'], ['index'])
    usage_info = {c: {'total': set(c_s)} for c, c_s in all_stats.items()}
    # Get indexes of used GPUs
    all_con_ids = exec.run_group_command(
        ctx.obj['hosts'], ctx.obj['user'], 'docker ps -q')
    for conn, conn_con_ids in all_con_ids.items():
        conn_gpus_used = set()
        for con_id in conn_con_ids:
            if not con_id:
                continue
            gpu_used = exec.get_container_gpu(conn, con_id)
            if not gpu_used:
                continue
            elif gpu_used == 'all':
                conn_gpus_used = usage_info[conn]['total']
                break
            else:
                conn_gpus_used.add(gpu_used)
        usage_info[conn]['used'] = conn_gpus_used
    # Get indexes of free GPUs by computing the difference between the set of
    # available GPUs and the set of used GPUs
    for conn, usage in usage_info.items():
        usage['free'] = usage['total'] - usage['used']
    # Run the docker run command on all free GPUs
    for conn, usage in usage_info.items():
        free_gpus = usage['free']
        if not free_gpus:
            continue
        for free_gpu in free_gpus:
            # Create new container name
            name = [ctx.obj['user'], free_gpu]
            if custom_name:
                name.append(custom_name)
            name = '-'.join(name)
            command = [
                base_command,
                '--name ' + name,
                '--env NVIDIA_VISIBLE_DEVICES=' + free_gpu,
                *docker_run_args
            ]
            conn.run(' '.join(command), hide=True)


if __name__ == '__main__':
    cli()
