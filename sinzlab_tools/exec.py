import re

from fabric import ThreadingGroup


def run_group_command(hosts, user, command):
    group = ThreadingGroup(*hosts, user=user)
    results = group.run(command, hide=True)
    outputs = {}
    for connection, result in sorted(results.items()):
        outputs[connection] = result.stdout.strip().split('\n')
    return outputs


def run_nvidia_smi(hosts, user, queries):
    command = [
        'nvidia-smi',
        '--format=csv,noheader,nounits',
        f'--query-gpu={",".join(queries)}'
    ]
    raw_all_stats = run_group_command(hosts, user, ' '.join(command))
    all_stats = {}
    for conn, raw_conn_stats in raw_all_stats.items():
        conn_stats = []
        for raw_gpu_stats in raw_conn_stats:
            gpu_stats = raw_gpu_stats.split(', ')
            if len(gpu_stats) == 1:
                gpu_stats = gpu_stats[0]
            conn_stats.append(gpu_stats)
        all_stats[conn] = conn_stats
    return all_stats


def get_container_gpu(conn, con_id):
    env = conn.run(
        'docker inspect --format "{{.Config.Env}}" ' + con_id,
        hide=True
    ).stdout
    match = re.search(r'NVIDIA_VISIBLE_DEVICES=(all|\d+)', env)
    return match.group(1) if match else ''


def get_total_gpus_indexes(hosts, user):
    all_gpu_indexes = run_nvidia_smi(hosts, user, ['index'])
    n_total = 0
    total_gpu_indexes = {}
    for conn, conn_gpu_indexes in all_gpu_indexes.values():
        conn_gpu_indexes = set(conn_gpu_indexes)
        n_total += len(conn_gpu_indexes)
        total_gpu_indexes[conn] = conn_gpu_indexes
    return n_total, total_gpu_indexes
