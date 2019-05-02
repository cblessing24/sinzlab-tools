import re

from fabric import ThreadingGroup


def run_group_command(hosts, user, command):
    if not isinstance(hosts, list):
        hosts = [hosts]
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
    for conn, conn_gpu_indexes in all_gpu_indexes.items():
        conn_gpu_indexes = set(conn_gpu_indexes)
        n_total += len(conn_gpu_indexes)
        total_gpu_indexes[conn] = conn_gpu_indexes
    return n_total, total_gpu_indexes


def get_used_gpu_indexes(hosts, user):
    all_con_ids = run_group_command(hosts, user, 'docker ps -q')
    n_used = 0
    used = {}
    for conn, conn_con_ids in all_con_ids.items():
        conn_used = set()
        for con_id in conn_con_ids:
            if not con_id:
                # No GPUs on the connection are currently in use because there
                # are no containers running on the connection
                continue
            used_gpu = get_container_gpu(conn, con_id)
            if not used_gpu:
                # The container does not use a GPU because the environment
                # variable NVIDIA_VISIBLE_DEVICES is not set inside the
                # container
                continue
            elif used_gpu == 'all':
                # All GPUs on the connection are in use because
                # NVIDIA_VISIBLE_DEVICES is set to 'all' inside the container
                _, total = get_total_gpus_indexes(conn.host, user)
                conn_used = set(total[conn])
                break
            else:
                conn_used.add(used_gpu)
        n_used += len(conn_used)
        used[conn] = conn_used
    return n_used, used


def get_free_gpu_indexes(hosts, user):
    n_total, total = get_total_gpus_indexes(hosts, user)
    n_used, used = get_used_gpu_indexes(hosts, user)
    n_free = n_total - n_used
    free = {}
    for (conn, conn_total), conn_used in zip(total.items(), used.values()):
        free[conn] = conn_total - conn_used
    return n_free, free
