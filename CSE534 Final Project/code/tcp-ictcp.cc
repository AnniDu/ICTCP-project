/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2016 ResiliNets, ITTC, University of Kansas
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Author: Truc Anh N. Nguyen <annguyen@ittc.ku.edu>
 *
 * James P.G. Sterbenz <jpgs@ittc.ku.edu>, director
 * ResiliNets Research Group  http://wiki.ittc.ku.edu/resilinets
 * Information and Telecommunication Technology Center (ITTC)
 * and Department of Electrical Engineering and Computer Science
 * The University of Kansas Lawrence, KS USA.
 */

#include "tcp-ictcp.h"
#include "ns3/tcp-socket-base.h"
#include "ns3/log.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("TcpIctcp");
NS_OBJECT_ENSURE_REGISTERED (TcpIctcp); 

TypeId
TcpIctcp::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::TcpIctcp")
    .SetParent<TcpNewReno> ()
    .AddConstructor<TcpIctcp> ()
    .SetGroupName ("Internet")
    .AddAttribute ("alpha", "Current measured throughput",
                   UintegerValue (3),
                   MakeUintegerAccessor (&TcpIctcp::m_beta),
                   MakeUintegerChecker<uint32_t> ())
    //newly add
    .AddAttribute("Count", "Decrease after three times",
      UintegerValue(0),
      MakeUintegerAccessor(&TcpIctcp::m_count),
      MakeUintegerChecker<uint32_t>())
    .AddAttribute("throughput","measured throughtput",
                   DoubleValue(0),
                   MakeDoubleAccessor(&TcpIctcp::m_bim),
                   MakeDoubleChecker<double>())
  ;
  return tid;
}

TcpIctcp::TcpIctcp (void)
  : TcpNewReno (),
    m_bim (0),   // newly add
    m_count (0), // newly add
    m_baseRtt (Time::Max ()),
    m_minRtt (Time::Max ()),
    m_cntRtt (0),
    m_doingVenoNow (true),
    m_diff (0),
    m_inc (true),
    m_ackCnt (0),
    m_beta (6)
{
  NS_LOG_FUNCTION (this);
}

TcpIctcp::TcpIctcp (const TcpIctcp& sock)
  : TcpNewReno (sock),
    m_bim(sock.m_bim), // newly add
    m_count(sock.m_count),
    m_baseRtt (sock.m_baseRtt),
    m_minRtt (sock.m_minRtt),
    m_cntRtt (sock.m_cntRtt),
    m_doingVenoNow (true),
    m_diff (0),
    m_inc (true),
    m_ackCnt (sock.m_ackCnt),
    m_beta (sock.m_beta)
{
  NS_LOG_FUNCTION (this);
}

TcpIctcp::~TcpIctcp (void)
{
  NS_LOG_FUNCTION (this);
}

Ptr<TcpCongestionOps>
TcpIctcp::Fork (void)
{
  return CopyObject<TcpIctcp> (this);
}

void
TcpIctcp::PktsAcked (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked,
                    const Time& rtt)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked << rtt);

  if (rtt.IsZero ())
    {
      return;
    }

  m_minRtt = std::min (m_minRtt, rtt);
  NS_LOG_DEBUG ("Updated m_minRtt= " << m_minRtt);


  m_baseRtt = std::min (m_baseRtt, rtt);
  NS_LOG_DEBUG ("Updated m_baseRtt= " << m_baseRtt);

  // Update RTT counter
  m_cntRtt++;
  NS_LOG_DEBUG ("Updated m_cntRtt= " << m_cntRtt);
}

void
TcpIctcp::EnableIctcp (Ptr<TcpSocketState> tcb)
{
  NS_LOG_FUNCTION (this << tcb);
  m_doingVenoNow = true;
  m_cntRtt = 0;
  m_minRtt = Time::Max ();
}

void
TcpIctcp::DisableIctcp ()
{
  NS_LOG_FUNCTION (this);

  m_doingVenoNow = false;
}

void
TcpIctcp::CongestionStateSet (Ptr<TcpSocketState> tcb,
                             const TcpSocketState::TcpCongState_t newState)
{
  NS_LOG_FUNCTION (this << tcb << newState);
  if (newState == TcpSocketState::CA_OPEN)
    {
      EnableIctcp (tcb);
      NS_LOG_LOGIC ("TcpIctcp is now on.");
    }
  else
    {
      DisableIctcp ();
      NS_LOG_LOGIC ("TcpIctcp is turned off.");
    }
}

void
TcpIctcp::IncreaseWindow (Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
  NS_LOG_FUNCTION (this << tcb << segmentsAcked);
  // newly add  

  double dib = EstimateDib(tcb);
  // change window size

  double y1 = 0.1;


  if(dib <= y1 || dib <= tcb->m_segmentSize / tcb->m_rcvWnd)
  { 
    if (tcb->m_rcvWnd < tcb->m_ssThresh)
    { // Slow start mode. Veno employs same slow start algorithm as NewReno's.
          NS_LOG_LOGIC ("We are in slow start, behave like NewReno.");
          segmentsAcked = TcpNewReno::SlowStart (tcb, segmentsAcked);
    }
    else
    { // Congestion avoidance mode
          NS_LOG_LOGIC ("We are in congestion avoidance, execute Veno additive "
                        "increase algo.");
          TcpNewReno::CongestionAvoidance (tcb, segmentsAcked);
    }
    NS_LOG_LOGIC ("Stage1");
    TcpNewReno::IncreaseWindow (tcb, segmentsAcked);
  }


  // end newly add

  // Reset cntRtt & minRtt every RTT
  m_cntRtt = 0;
  m_minRtt = Time::Max ();
}

std::string
TcpIctcp::GetName () const
{
  return "TcpIctcp";
}


double
TcpIctcp::EstimateDib(Ptr<const TcpSocketState> tcb){
  // compute measured throughput

  double beta = 0.5;
  // compute sample current throughput

  uint32_t segCwnd = tcb->GetCwndInSegments();
  double bis = m_baseRtt.GetSeconds() * segCwnd;

  m_bim = std::max(bis,beta * m_bim + (1-beta) * bis);

  // compute expected throughput
  
  double bie = std::max(m_bim,(double)(tcb->m_rcvWnd.Get() / m_baseRtt.GetSeconds()));

  // compute dib

  double dib = (bie - m_bim)/bie;

  return dib;
}

uint32_t
TcpIctcp::GetSsThresh (Ptr<const TcpSocketState> tcb,
                      uint32_t bytesInFlight)
{
  //newly add
  NS_LOG_FUNCTION (this << tcb << bytesInFlight);
    double y2 = 0.5;
    double dib = EstimateDib(tcb);
    if(dib > y2 && m_count >= 2){
      m_count=0;
      return tcb->m_rcvWnd.Get() - tcb->m_segmentSize;
    }
    else if(dib > y2){
      m_count++;
      return tcb->m_rcvWnd.Get();
    }
    else{
      return tcb->m_rcvWnd.Get();
    }
  // if (m_diff < m_beta)
  //   {
  //     // random loss due to bit errors is most likely to have occurred,
  //     // we cut cwnd by 1/5
  //     NS_LOG_LOGIC ("Random loss is most likely to have occurred, "
  //                   "cwnd is reduced by 1/5");
  //     static double tmp = 4.0/5.0;
  //     return std::max (static_cast<uint32_t> (bytesInFlight * tmp),
  //                      2 * tcb->m_segmentSize);
  //   }
  // else
  //   {
  //     // congestion-based loss is most likely to have occurred,
  //     // we reduce cwnd by 1/2 as in NewReno
  //     NS_LOG_LOGIC ("Congestive loss is most likely to have occurred, "
  //                   "cwnd is halved");
  //    return TcpNewReno::GetSsThresh (tcb, bytesInFlight);
  //  }
}

} // namespace ns3
