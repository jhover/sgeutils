
import os
import pwd
import subprocess


def get_username():
    return pwd.getpwuid( os.getuid() )[ 0 ]


def parse_output(lines):
    lod = []
    current = None
    for line in lines:
        if line.startswith("======="):
            if current is not None:
                lod.append(current)
            current = {}
        else:
            key = line[0:13].strip()
            value = line[13:].strip()
            #print(f"{key} = {value}")
            if key == "jobnumber":
                current['jobnumber'] = value
            elif key == "jobname":
                current['jobname'] = value
            elif key == "exit_status":
                current["exit_status"] = value
            elif key == "slots":
                current['slots'] = value
            elif key == "wallclock":
                current["wallclock"] = value
            elif key == "start_time":
                current["start_time"] = value
            elif key == "end_time":
                current["end_time"] = value
            elif key == "maxvmem":
                current["maxvmem"] = value
            elif key == "maxrss":
                current["maxrss"] = value
            elif key == "pe_taskid":
                current["pe_taskid"] = value
            elif key == "submit_cmd":
                current["submit_cmd"] = value

    return lod


def get_history(days=1, user=get_username()):
    cmd = f"qacct -j -o {user}"
    if days is not None:
        cmd += f" -d {days} "
        cmd += f" -o {user} "
    result = subprocess.check_output( cmd, shell=True, text=True )
    lines = result.split('\n')
    joblist = parse_output(lines)
    #print(f"got {len(info)} jobs")
    joblist.sort(key=lambda x: int(x['jobnumber']))
    joblist.reverse()
    return joblist


def printjoblist(joblist, header=False, nlines=0, memorystat=['maxvmem']):
#    fields = ["jobnumber", "jobname", "pe_taskid", "ru_wallclock", "slots", "maxvmem", "exit_status","submit_cmd"  ]
    if memorystat == ['both']:
        memorystat = ['maxvmem', 'maxrss']
    fields = (
        [
            ("jobnumber", 10),
            ("jobname", 25),
            ( "pe_taskid", 6),
            ( "start_time", 22),
            ("end_time", 22 ),
            ("wallclock", 10),
            ( "slots", 7 )
        ]
        + list(zip(memorystat, [10]*len(memorystat)))
        + [( "exit_status", 6 )]
    )
    hlist = []
    slist = []
    if header:
        s=""
        for (f, w) in fields:
           value = f
           value = value[:(w -1)]  # strip it if longer than field.
           s += f"{value}"
           pad = ' ' * (w - len(value))
           s += pad
        hlist.append(s)
        hline = '-' * sum([f[1] for f in fields])
        hlist.append(hline)
    for jobdict in joblist:
        s=""
        for (f, w) in fields:
            value = jobdict[f]
            if f == 'wallclock':
                value = int(float(value))
                if value >= 86400:
                    days = True
                else:
                    days = False
                value = convert_seconds(value, days=days)
                new_value = []
                for i, val in enumerate(value):
                    if i == 0:
                        new_value.append(f'{val:2d}')
                    else:
                        new_value.append(f'{val:02d}')
                value = ':'.join(new_value)
            elif f.endswith('_time'):
                value = value[:-4]
            value = value[:(w -1)]  # strip it if longer than field.
            s += f"{value}"
            pad = ' ' * (w - len(value))
            s += pad
        slist.append(s)
    if nlines > 0:
        slist = slist[:nlines]

    out = '\n'.join(hlist + slist)
    out = out + '\n'
    return out


def convert_seconds(seconds, days=False):
    """Convert seconds to hours, minutes, and seconds.

    Args:
        seconds: integer. Number of seconds to be converted.
        days: boolean. If True, a 4-member tuple is returned
            with days.

    Returns:
        A tuple of 3 integers. Seconds converted to
        hours, minutes, seconds. If days=True, then days is
        included and a 4 member tuple is returned.
    """
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if days:
        d, h = divmod(h, 24)
        return d, h, m, s
    else:
        return h, m, s