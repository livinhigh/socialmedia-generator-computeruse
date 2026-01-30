#!/bin/bash
echo "starting noVNC proxies"

VNC_PORT_LIST=${VNC_PORTS:-"5900 5901"}
NOVNC_PORT_LIST=${NOVNC_PORTS:-"6080 6081"}

read -ra VNC_PORT_ARRAY <<< "$VNC_PORT_LIST"
read -ra NOVNC_PORT_ARRAY <<< "$NOVNC_PORT_LIST"

if [ ${#VNC_PORT_ARRAY[@]} -ne ${#NOVNC_PORT_ARRAY[@]} ]; then
    echo "VNC port count (${#VNC_PORT_ARRAY[@]}) does not match noVNC port count (${#NOVNC_PORT_ARRAY[@]})" >&2
    exit 1
fi

log_paths=()

for i in "${!VNC_PORT_ARRAY[@]}"; do
    vnc_port=${VNC_PORT_ARRAY[$i]}
    novnc_port=${NOVNC_PORT_ARRAY[$i]}
    log_path=/tmp/novnc_display$((i + 1)).log

    /opt/noVNC/utils/novnc_proxy \
        --vnc localhost:${vnc_port} \
        --listen ${novnc_port} \
        --web /opt/noVNC \
        > ${log_path} 2>&1 &

    log_paths[$i]=$log_path
done

timeout=10
for novnc_port in "${NOVNC_PORT_ARRAY[@]}"; do
    temp_timeout=$timeout
    while [ $temp_timeout -gt 0 ]; do
        if netstat -tuln | grep -q ":${novnc_port} "; then
            echo "noVNC started successfully on port ${novnc_port}"
            break
        fi
        sleep 1
        ((temp_timeout--))
    done

    if [ $temp_timeout -eq 0 ]; then
        echo "noVNC failed to start on port ${novnc_port}" >&2
        exit 1
    fi
done

echo "All noVNC proxies started successfully"
