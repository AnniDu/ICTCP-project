from __future__ import division
import dpkt
import datetime
import socket
import binascii
import math
def main():
    f = open('N1-recieved-packets7-7-0.pcap', 'rb')
    pcap = dpkt.pcap.Reader(f)
    totalNum = 0
    sourIp = None
    destIp = None
    sendMap = {}
    # A-1
    tcpNum = 0
    # A-2a
    win_scale_EachFlow = {}
    total_EachRtt = {}
    total_EachTransaction = {}
    transaction_2String = {}
    transaction_2Index = {}
    is_Retransmiss = []
    # A-2b
    flowPort = []
    flowSize = {}
    startTime = {}
    endTime = {}
    # A-2c
    packSend = {}
    packRecv = {}
    retrans_num = {}
    # A-2d
    mss = {}

    diffSour = []
    diffSourSeq = {}
    num_retrans = 0
    total_pack_send = 0
    for ts, buf in pcap:  # time stamp and complete packet
        # print type(ts)
        totalNum += 1
        if(len(buf) == 64):
            continue


        totalLen = int(binascii.hexlify(buf)[32:36], 16)
        # IP part******************************************************
        srcIp = binascii.hexlify(buf)[52:60]
        # print str(srcIp)
        dstIp = binascii.hexlify(buf)[60:68]
        # print str(dstIp)
        ipHeaderLen = 20
        # IP part******************************************************
        # if (sourIp == None):
        #     sourIp = srcIp

        if (destIp == None):
            destIp = dstIp
        # TCP header part**********************************************
        headerStart = buf[34:]
        seq = int(binascii.hexlify(headerStart)[8:16],16)
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
        if(destIp == dstIp):
            total_pack_send += 1
            if (not diffSourSeq.__contains__(srcIp)):
                # diffSour.append(srcIp)
                diffSourSeq[srcIp] = []
                diffSourSeq.get(srcIp).append(seq)
            else:
                if(diffSourSeq.get(srcIp).__contains__(seq)):
                    # print totalNum
                    # print int(seq)
                    num_retrans += 1
                else:
                    diffSourSeq.get(srcIp).append(seq)
        else:
            continue

    print "loss time: ", num_retrans , "|pack send: ", total_pack_send , "|rate: ", num_retrans / total_pack_send
        # if (srcIp == sourIp):
        #     tuple = (int(seq, 16) + tcpSegLen, ackNum)
        #     if (int(syn, 2) == 1):
        #         tcpNum += 1
        #     if (not sendMap.__contains__(sport)):
        #         flowPort.append(sport)
        #         sendMap[sport] = {tuple : (ts, seq, tcpSegLen, win, totalNum)}
        #         total_EachRtt[sport] = 0
        #         total_EachTransaction[sport] = 0
        #         transaction_2String[sport] = ""
        #         transaction_2Index[sport] = 1
        #         flowSize[sport] = len(buf)
        #         startTime[sport] = ts
        #         packSend[sport] = 1
        #         packRecv[sport] = 0
        #         win_scale_EachFlow[sport] = int(binascii.hexlify(buf[-1]), 16)
        #         retrans_num[sport] = 0
        #     else:#contain sport
        #         flowSize[sport] = flowSize.get(sport) + len(buf)
        #         packSend[sport] = packSend.get(sport) + 1
        #         eachFlow = sendMap.get(sport)
        #         if(eachFlow.__contains__(tuple)):#cover
        #             retrans_num[sport] = retrans_num.get(sport) + 1
        #             eachFlow[tuple] = (ts, seq, tcpSegLen, win, totalNum)
        #             is_Retransmiss.append(tuple)
        #         else:#new thing
        #             eachFlow[tuple] = (ts, seq, tcpSegLen, win, totalNum)
        # elif (srcIp == destIp):
        #     flow = sendMap.get(dport)
        #     packRecv[dport] = packRecv.get(dport) + 1
        #     #3-way handshake case
        #     if (int(syn, 2) == 1) and (int(ack, 2) == 1):
        #         mss[dport] = int(binascii.hexlify(headerStart)[44:48], 16)
        #         for i in flow:
        #             if (i[0] == int(ackNum, 16) - 1):
        #                 total_EachRtt[dport] = total_EachRtt.get(dport) + (ts - flow.get(i)[0])
        #                 total_EachTransaction[dport] = total_EachTransaction.get(dport) + 1
        #                 del flow[i]
        #                 break
        #     #close cases
        #     elif (int(fin, 2) == 1) and (int(ack, 2) == 1):
        #         endTime[dport] = ts
        #         for i in flow:
        #             if (i[0] == int(ackNum, 16) - 1):
        #                 total_EachRtt[dport] = total_EachRtt.get(dport) + (ts - flow.get(i)[0])
        #                 total_EachTransaction[dport] = total_EachTransaction.get(dport) + 1
        #                 del flow[i]
        #                 break
        #     else:
        #         tuple = (int(ackNum,16), seq)# key = (int(seq, 16) + tcpSegLen, ackNum) value = (ts, seq, tcpSegLen, win, totalNum)
        #         # duplicated case
        #         if(flow.get(tuple) == None):
        #             continue
        #         if (not is_Retransmiss.__contains__(tuple)):
        #             total_EachRtt[dport] = total_EachRtt.get(dport) + (ts - flow.get(tuple)[0])
        #             total_EachTransaction[dport] = total_EachTransaction.get(dport) + 1
        #
        #         if (transaction_2Index.get(dport) <= 2):
        #             curString = transaction_2String.get(dport) + str(flow.get(tuple)[4]) + " " + str(transaction_2Index.get(dport)) \
        #                         + ": Sending part of flow: Sequence num: " + str(flow.get(tuple)[1]) \
        #                         + "  ||Ack num: " + str(seq) + " ||Receive Window Size: " + str(flow.get(tuple)[3] * pow(2, win_scale_EachFlow.get(dport))) + "\n" \
        #                         + str(totalNum) + " " + str(transaction_2Index.get(dport)) + ": Response part of flow: Sequence num: " \
        #                         + str(seq) + "  ||Ack num: " + str(ackNum) + " ||Receive Window Size: " + str(win * pow(2, win_scale_EachFlow.get(dport))) + "\n"
        #             transaction_2Index[dport] = transaction_2Index.get(dport) + 1
        #             transaction_2String[dport] = curString
        #         del flow[tuple]
    # flowLossRate = {}
    # print "Part A-1 answer(how many flow):"
    # get_flow_num(tcpNum)
    # print "\nPart A-2a answer(first two transaction information):"
    # get_transaction_info(transaction_2String)
    # print "Part A-2b answer(throughput):"
    # get_throughput(flowPort, flowSize, endTime, startTime)
    # print "\nPart A-2c answer(Loss Rate):"
    # get_loss_rate(flowPort, flowLossRate, packSend, packRecv, retrans_num)
    # print "\nPart A-2d answer():"
    # get_avgRtt(flowPort, total_EachRtt, total_EachTransaction, mss, flowLossRate)

    f.close()

def get_flow_num(tcpNum):
    print tcpNum

def get_transaction_info(transaction_string):
    for i in transaction_string:
        print transaction_string[i]

def get_throughput(flowPort, flowSize, endTime, startTime):
    for i in range(0, len(flowPort)):
        port = flowPort[i]
        print "Flow " + str(i + 1) + " Bytes send:", flowSize.get(port), "||Duration:", endTime.get(port) - startTime.get(port)\
            , "||Throughput(Byte/s):", flowSize.get(port) / (endTime.get(port) - startTime.get(port))

def get_loss_rate(flowPort, flowLossRate, packSend, packRecv, retrans_num):
    for i in range(0,len(flowPort)):
        port = flowPort[i]
        # flowLossRate[port] = (packSend.get(port) - packRecv.get(port)) / packSend.get(port)
        flowLossRate[port] = (retrans_num.get(port)) / packSend.get(port)
        print "Flow " + str(i + 1) + ": Num of Retransmission: ",retrans_num.get(port), "||Num of Packets send:", packSend.get(port), "||Loss Rate:", flowLossRate.get(port)

def get_avgRtt(flowPort, total_EachRtt, total_EachTransaction, mss, flowLossRate):
    for i in range(0, len(flowPort)):
        port = flowPort[i]
        tRtt = total_EachRtt.get(port) / total_EachTransaction.get(port)
        tMss = mss.get(port)
        tP = flowLossRate.get(port)
        theory_throughput = None
        if(tP == 0):
            theory_throughput = (math.sqrt(1.5) * tMss) / tRtt
        else:
            theory_throughput = (math.sqrt(1.5) * tMss) / (math.sqrt(tP) * tRtt)
        print "RTT is", tRtt, "||Theoretical Throughput is", theory_throughput

if __name__ == '__main__':
        main()