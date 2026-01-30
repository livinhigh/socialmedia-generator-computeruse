#!/bin/bash
echo "starting vnc servers"

DISPLAY_LIST=${DISPLAY_NUMS:-"1 2"}
VNC_PORT_LIST=${VNC_PORTS:-"5900 5901"}

read -ra DISPLAY_ARRAY <<< "$DISPLAY_LIST"
read -ra VNC_PORT_ARRAY <<< "$VNC_PORT_LIST"

if [ ${#DISPLAY_ARRAY[@]} -ne ${#VNC_PORT_ARRAY[@]} ]; then
    echo "Display count (${#DISPLAY_ARRAY[@]}) does not match VNC port count (${#VNC_PORT_ARRAY[@]})" >&2
    exit 1
fi

pids=()
log_paths=()

for i in "${!DISPLAY_ARRAY[@]}"; do
    display_num=${DISPLAY_ARRAY[$i]}
    vnc_port=${VNC_PORT_ARRAY[$i]}
    log_path=/tmp/x11vnc_display${display_num}_stderr.log

    (x11vnc -display :${display_num} \
        -forever \
        -shared \
        -wait 50 \
        -rfbport ${vnc_port} \
        -nopw \
        2>${log_path}) &

    pids[$i]=$!
    log_paths[$i]=$log_path
done

timeout=10
for i in "${!VNC_PORT_ARRAY[@]}"; do
    port=${VNC_PORT_ARRAY[$i]}
    temp_timeout=$timeout
    while [ $temp_timeout -gt 0 ]; do
        if netstat -tuln | grep -q ":${port} "; then
            echo "x11vnc started successfully on port ${port}"
            break
        fi
        sleep 1
        ((temp_timeout--))
    done

    if [ $temp_timeout -eq 0 ]; then
        echo "x11vnc failed to start on port ${port}, stderr output:" >&2
        cat "${log_paths[$i]}" >&2
        exit 1
    fi
done

for log_path in "${log_paths[@]}"; do
    : > "$log_path"
done

# Monitor all x11vnc processes in the background
(
    while true; do
        for i in "${!pids[@]}"; do
            pid=${pids[$i]}
            display_num=${DISPLAY_ARRAY[$i]}
            log_path=${log_paths[$i]}

            if ! kill -0 $pid 2>/dev/null; then
                echo "x11vnc display :${display_num} process crashed, restarting..." >&2
                if [ -f "$log_path" ]; then
                    echo "x11vnc display :${display_num} stderr output:" >&2
                    cat "$log_path" >&2
                    rm "$log_path"
                fi
                exec "$0"
            fi
        done

        sleep 5
    done
) &
