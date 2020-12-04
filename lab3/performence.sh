sv1 ping -c 7 sv6
pingall

sv5 iperf -s &> sv5.log &
sv6 iperf -s &> sv6.log &

sv13 iperf -s &> sv13.log &
sv14 iperf -s &> sv14.log &



sv1 iperf -c sv5 -t 60 &> sv1.log &
sv4 iperf -c sv6 -t 60 &> sv4.log &

sv9 iperf -c sv13 -t 60 &> sv9.log &
sv11 iperf -c sv14 -t 60 &> sv11.log &



