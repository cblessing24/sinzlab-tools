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
    all_stats = run_group_command(hosts, user, ' '.join(command))
    for conn, conn_stats in all_stats.items():
        all_stats[conn] = [gpu_stats.split(', ') for gpu_stats in conn_stats]
    return all_stats
