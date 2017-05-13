from __future__ import division
import dpkt
import binascii
import math


def main():
    f = open('N1-recieved-packets15-7-0.pcap', 'rb')
    pcap = dpkt.pcap.Reader(f)
    totalNum = 0
    sourIp = None
    destIp = None
    sendMap = {}

    tcpNum = 0

    win_scale_EachFlow = {}
    total_EachRtt = {}
    total_EachTransaction = {}
    transaction_2String = {}
    transaction_2Index = {}
    is_Retransmiss = []

    flowPort = []
    flowSize = {}
    startTime = {}
    endTime = {}

    packSend = {}
    packRecv = {}

    mss = {}

    ack_pkt_num_EachFlow = {}
    ack_pkt_num_Checked = {}
    cwnd_EachFlow = {}

    time_out_EachFlow = {}  # the Rto for each flow
    triple_Dup_num_EachFlow = {}  # the number that retrans by triple dup
    rto_num_EachFlow = {}  # the number that retrans by rto
    retrans_num = {}

    globalStartTime = 0
    globalEndTime = 0
    globalSendNum = 0
    globalReceNum = 0
    f = open("test.txt", "a")
    # f.write("loss Rate:     goodput:     loss Rate WireShark:\n")
    for ts, buf in pcap:  # time stamp and complete packet
        # print type(ts)
        totalNum += 1
        if (len(buf) == 64):
            continue
        if (globalStartTime == 0):
            globalStartTime = ts
        globalEndTime = ts

        # print totalNum
        totalLen = int(binascii.hexlify(buf)[32:36], 16)
        # IP part******************************************************
        srcIp = binascii.hexlify(buf)[52:60]
        dstIp = binascii.hexlify(buf)[60:68]
        ipHeaderLen = 20
        # IP part******************************************************
        if (destIp == None):
            destIp = dstIp
        # TCP header part**********************************************
        headerStart = buf[34:]
        seq = binascii.hexlify(headerStart)[8:16]
        ackNum = binascii.hexlify(headerStart)[16:24]

        ran = bin(int(binascii.hexlify(headerStart)[24:28], 16))[2:]
        win = int(binascii.hexlify(headerStart)[28:32], 16)
        tcpHeaderLen = int(ran[0:6], 2)
        flags = ran[10:16]
        urg = flags[0]
        ack = flags[1]
        psh = flags[2]
        rst = flags[3]
        syn = flags[4]
        fin = flags[5]
        tcpSegLen = totalLen - ipHeaderLen - tcpHeaderLen

        if (destIp == dstIp):
            globalSendNum += 1
            tuple = (int(seq, 16) + tcpSegLen, ackNum)
            # if (int(syn, 2) == 1):
            #     tcpNum += 1
            if (not sendMap.__contains__(srcIp)):
                tcpNum += 1
                flowPort.append(srcIp)
                sendMap[srcIp] = {tuple: (ts, seq, tcpSegLen, win, totalNum)}
                total_EachRtt[srcIp] = 0
                total_EachTransaction[srcIp] = 0
                transaction_2String[srcIp] = ""
                transaction_2Index[srcIp] = 1
                flowSize[srcIp] = len(buf)
                startTime[srcIp] = ts
                packSend[srcIp] = 1
                packRecv[srcIp] = 0
                win_scale_EachFlow[srcIp] = int(binascii.hexlify(buf[-1]), 16)
                ack_pkt_num_EachFlow[srcIp] = []
                ack_pkt_num_Checked[srcIp] = []
                triple_Dup_num_EachFlow[srcIp] = 0
                rto_num_EachFlow[srcIp] = 0
                retrans_num[srcIp] = 0
            else:  # contain srcIp
                flowSize[srcIp] = flowSize.get(srcIp) + len(buf)
                packSend[srcIp] = packSend.get(srcIp) + 1
                eachFlow = sendMap.get(srcIp)
                if (eachFlow.__contains__(tuple)):  # cover
                    retrans_num[srcIp] = retrans_num.get(srcIp) + 1
                    loss_pac = eachFlow.get(tuple)
                    rto = time_out_EachFlow.get(srcIp)
                    if (ts - loss_pac[0] < rto):
                        triple_Dup_num_EachFlow[srcIp] = triple_Dup_num_EachFlow.get(srcIp) + 1
                    elif (ts - loss_pac[0] >= rto):
                        rto_num_EachFlow[srcIp] = rto_num_EachFlow.get(srcIp) + 1
                    eachFlow[tuple] = (ts, seq, tcpSegLen, win, totalNum)
                    is_Retransmiss.append(tuple)
                else:  # new thing
                    eachFlow[tuple] = (ts, seq, tcpSegLen, win, totalNum)
        else:
            globalReceNum += 1
            flow = sendMap.get(dstIp)
            sending_Tuple = None
            packRecv[dstIp] = packRecv.get(dstIp) + 1
            # 3-way handshake case
            if (int(syn, 2) == 1) and (int(ack, 2) == 1):

                mss[dstIp] = int(binascii.hexlify(headerStart)[44:48], 16)
                if (mss[dstIp]) > 2190:
                    cwnd_EachFlow[dstIp] = [2 * mss[dstIp]]
                elif (mss[dstIp] > 1095) and (mss[dstIp] <= 2190):
                    cwnd_EachFlow[dstIp] = [3 * mss[dstIp]]
                elif (mss[dstIp] <= 1095):
                    cwnd_EachFlow[dstIp] = [4 * mss[dstIp]]
                for i in flow:
                    if (i[0] == int(ackNum, 16) - 1):
                        sending_Tuple = flow.get(i)
                        total_EachRtt[dstIp] = total_EachRtt.get(dstIp) + (ts - sending_Tuple[0])
                        time_out_EachFlow[dstIp] = 2 * (ts - sending_Tuple[0])
                        total_EachTransaction[dstIp] = total_EachTransaction.get(dstIp) + 1
                        del flow[i]
                        break
            # close cases
            elif (int(fin, 2) == 1) and (int(ack, 2) == 1):
                endTime[dstIp] = ts
                for i in flow:
                    if (i[0] == int(ackNum, 16) - 1):
                        sending_Tuple = flow.get(i)
                        total_EachRtt[dstIp] = total_EachRtt.get(dstIp) + (ts - sending_Tuple[0])
                        total_EachTransaction[dstIp] = total_EachTransaction.get(dstIp) + 1
                        del flow[i]
                        break
            else:
                tuple = (int(ackNum, 16), seq)  # key = (int(seq, 16) + tcpSegLen, ackNum) value = (ts, seq, tcpSegLen, win, totalNum)
                sending_Tuple = flow.get(tuple)
                # duplicated case
                if (sending_Tuple == None):
                    continue
                if (not is_Retransmiss.__contains__(tuple)):
                    total_EachRtt[dstIp] = total_EachRtt.get(dstIp) + (ts - sending_Tuple[0])
                    total_EachTransaction[dstIp] = total_EachTransaction.get(dstIp) + 1

                if (transaction_2Index.get(dstIp) <= 2):
                    curString = transaction_2String.get(dstIp) + str(flow.get(tuple)[4]) + " " + str(transaction_2Index.get(dstIp)) \
                                + ": Sending part of flow: Sequence num: " + str(flow.get(tuple)[1]) \
                                + "  ||Ack num: " + str(seq) + " ||Receive Window Size: " + str(flow.get(tuple)[3] * pow(2, win_scale_EachFlow.get(dstIp))) + "\n" \
                                + str(totalNum) + " " + str(transaction_2Index.get(dstIp)) + ": Response part of flow: Sequence num: " \
                                + str(seq) + "  ||Ack num: " + str(ackNum) + " ||Receive Window Size: " + str(win * pow(2, win_scale_EachFlow.get(dstIp))) + "\n"
                    transaction_2Index[dstIp] = transaction_2Index.get(dstIp) + 1
                    transaction_2String[dstIp] = curString

                # cwnd size has problem for the dup cases
                ack_pkt_num_EachFlow.get(dstIp).append(totalNum)
                cwnd_now = cwnd_EachFlow.get(dstIp)[-1]
                eMss = mss.get(dstIp)
                for i in ack_pkt_num_EachFlow.get(dstIp):
                    if (i > sending_Tuple[4] + 1) and (i < totalNum):  # and (i not in ack_pkt_num_Checked.get(dport)):
                        cwnd_now += eMss
                        ack_pkt_num_Checked.get(dstIp).append(i)
                for i in ack_pkt_num_Checked.get(dstIp):
                    ack_pkt_num_Checked.get(dstIp).remove(i)
                del ack_pkt_num_Checked.get(dstIp)[:]
                cwnd_EachFlow.get(dstIp).append(cwnd_now)
                del flow[tuple]


    flowLossRate = {}
    print "how many server send together):"
    num = get_flow_num(tcpNum)
    print num
    print "total throughput:"
    throughput = get_throughput(flowPort, flowSize, globalEndTime, globalStartTime)
    print "\nLoss Rate:"
    totalRetran, totalPackSend = get_loss_rate(flowPort, flowLossRate, packSend, packRecv, retrans_num)
    f.write(str(totalRetran * 100/ totalPackSend) + "%")
    goodput = (1 - totalRetran/totalPackSend) * throughput
    f.write("    " + str(goodput))
    print "\ngoodput: ", "\n", goodput

    print "\nRatio TCP timeout: "
    timeoutNum = get_transmission_num(flowPort, triple_Dup_num_EachFlow, rto_num_EachFlow)
    print "\n", timeoutNum/totalPackSend

    print "WireShark loss rate: ", (globalSendNum - globalReceNum)*100 / globalSendNum,"%"
    f.write("    " + str((globalSendNum - globalReceNum)*100 / globalSendNum) + "%\n")
# part B function
def get_congestion_win(flowPort, cwnd_EachFlow):
    for i in range(0, len(flowPort)):
        port = flowPort[i]
        print "Initial window size:", cwnd_EachFlow.get(port)[0], "||first five window size", cwnd_EachFlow.get(port)[2:7]


def get_transmission_num(flowPort, triple_Dup_num_EachFlow, rto_num_EachFlow):
    timeoutNum = 0
    triple_Dup_num = 0
    for i in range(0, len(flowPort)):
        port = flowPort[i]
        timeoutNum += rto_num_EachFlow[port]
        triple_Dup_num += triple_Dup_num_EachFlow[port]
        # print "Flow", i + 1, "transmission number of triple duplicate ack: ", triple_Dup_num_EachFlow[port]
        # print "Flow", i + 1, "transmission number of time out: ", rto_num_EachFlow[port]
    return timeoutNum


# part A function
def get_flow_num(tcpNum):
    return tcpNum


def get_transaction_info(transaction_string):
    for i in transaction_string:
        print transaction_string[i]


def get_throughput(flowPort, flowSize, endTime, startTime):
    totalByte = 0
    for i in range(0, len(flowPort)):
        port = flowPort[i]
        totalByte += flowSize.get(port)
        # print "Flow " + str(i + 1) + " Bytes send:", flowSize.get(port), "||Duration:", endTime.get(port) - startTime.get(port)\
        #     , "||Throughput(Byte/s):", flowSize.get(port) / (endTime.get(port) - startTime.get(port))
    print "Bytes send: ", totalByte, "|Duration: ", (endTime - startTime), "|Throughput(Mbps):", totalByte * 8/ (100000*(endTime - startTime))
    return totalByte * 8/ (100000*(endTime - startTime))


def get_loss_rate(flowPort, flowLossRate, packSend, packRecv, retrans_num):
    totalRetran = 0
    totalPackSend = 0
    for i in range(0, len(flowPort)):
        port = flowPort[i]
        # flowLossRate[port] = (packSend.get(port) - packRecv.get(port)) / packSend.get(port)
        totalRetran += retrans_num.get(port)
        totalPackSend += packSend.get(port)
        # flowLossRate[port] = (retrans_num.get(port)) / packSend.get(port)
        # print "Flow " + str(i + 1) + ": Num of Retransmission: ",retrans_num.get(port), "||Num of Packets send:", packSend.get(port), "||Loss Rate:", flowLossRate.get(port)
    print "Num of Retransmission:", totalRetran, "|Num of Packets send: ", totalPackSend, "|Loss Rate", totalRetran / totalPackSend
    return totalRetran,totalPackSend


def get_avgRtt(flowPort, total_EachRtt, total_EachTransaction, mss, flowLossRate):
    for i in range(0, len(flowPort)):
        port = flowPort[i]
        tRtt = total_EachRtt.get(port) / total_EachTransaction.get(port)
        tMss = mss.get(port)
        tP = flowLossRate.get(port)
        theory_throughput = None
        if (tP == 0):
            theory_throughput = (math.sqrt(1.5) * tMss) / tRtt
        else:
            theory_throughput = (math.sqrt(1.5) * tMss) / (math.sqrt(tP) * tRtt)
        print "RTT is", tRtt, "||Theoretical Throughput is", theory_throughput


if __name__ == '__main__':
    main()