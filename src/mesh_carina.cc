/*
 * Wireless Mesh Networks
 * By Carina T. de Oliveira
 */

#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "ns3/applications-module.h"
#include "ns3/wifi-module.h"
#include "ns3/mesh-module.h"
#include "ns3/mobility-module.h"
#include "ns3/mesh-helper.h"
#include "ns3/flow-monitor-module.h"

#include <iostream>
#include <sstream>
#include <fstream>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("TestMeshScript");
class MeshTest
{
public:
  /// Init test
  MeshTest ();
  /// Configure test from command line arguments
  void Configure (int argc, char ** argv);
  /// Run test
  int Run ();
private:
  int       m_xSize;

  int       m_ySize;
  int       m_cliente;
  double    m_step;
  double    m_randomStart;
  double    m_totalTime;
  double    m_packetInterval;
  uint16_t  m_packetSize;
  uint32_t  m_nIfaces;
  bool      m_chan;
  bool      m_pcap;
  std::string m_stack;
  std::string m_root;
  /// List of network nodes
  NodeContainer nodes;
  /// List of all mesh point devices
  NetDeviceContainer meshDevices;
  //Addresses of interfaces:
  Ipv4InterfaceContainer interfaces;
  // MeshHelper. Report is not static methods
  MeshHelper mesh;
private:
  /// Create nodes and setup their mobility
  void CreateNodes ();
  /// Install internet m_stack on nodes
  void InstallInternetStack ();
  /// Install applications
  void InstallApplication ();
  /// Print mesh devices diagnostics
  void Report ();
};
MeshTest::MeshTest () :
  m_xSize (3),
  m_ySize (3),
  m_cliente (2),
  m_step (100.0),
  m_randomStart (0.1),
  m_totalTime (100.0),
  m_packetInterval (0.1),
  m_packetSize (1024),
  m_nIfaces (1),
  m_chan (true),
  m_pcap (false),
  m_stack ("ns3::Dot11sStack"),
  m_root ("ff:ff:ff:ff:ff:ff")
{
}
///////////////////////////////////////////////////////////////////////////
//                                                                       //
// Configure Parameters                                                  //
//                                                                       //
///////////////////////////////////////////////////////////////////////////
void
MeshTest::Configure (int argc, char *argv[])
{
  CommandLine cmd;
  cmd.AddValue ("x-size", "Number of nodes in a row grid. [6]", m_xSize);
  cmd.AddValue ("y-size", "Number of rows in a grid. [6]", m_ySize);
  cmd.AddValue ("cliente", "Number do nó cliente. [1]", m_cliente);
  cmd.AddValue ("step",   "Size of edge in our grid, meters. [100 m]", m_step);
  /*
   * As soon as starting node means that it sends a beacon,
   * simultaneous start is not good.
   */
  cmd.AddValue ("start",  "Maximum random start delay, seconds. [0.1 s]", m_randomStart);
  cmd.AddValue ("time",  "Simulation time, seconds [100 s]", m_totalTime);
  cmd.AddValue ("packet-interval",  "Interval between packets in UDP ping, seconds [0.001 s]", m_packetInterval);
  cmd.AddValue ("packet-size",  "Size of packets in UDP ping", m_packetSize);
  cmd.AddValue ("interfaces", "Number of radio interfaces used by each mesh point. [1]", m_nIfaces);
  cmd.AddValue ("channels",   "Use different frequency channels for different interfaces. [0]", m_chan);
  cmd.AddValue ("pcap",   "Enable PCAP traces on interfaces. [0]", m_pcap);
  cmd.AddValue ("stack",  "Type of protocol stack. ns3::Dot11sStack by default", m_stack);
  cmd.AddValue ("root", "Mac address of root mesh point in HWMP", m_root);

  cmd.Parse (argc, argv);
  NS_LOG_DEBUG ("Grid:" << m_xSize << "*" << m_ySize);
  NS_LOG_DEBUG ("Simulation time: " << m_totalTime << " s");

  std::cout << "size " << m_xSize << 'x' << m_ySize << std::endl;
}
///////////////////////////////////////////////////////////////////////////
//                                                                       //
// CREATE NODES                                                          //
//                                                                       //
///////////////////////////////////////////////////////////////////////////
void
MeshTest::CreateNodes ()
{

  NS_LOG_INFO ("CreateNodes.");
  std::cout << "1. Criando nós na rede...\n";

  nodes.Create (m_ySize*m_xSize);

  //------------------------------//
  // PHY CONFIGURATION
  std::cout << "-- 1.1 Configurando PHY\n";

  YansWifiPhyHelper wifiPhy = YansWifiPhyHelper::Default ();
  YansWifiChannelHelper wifiChannel = YansWifiChannelHelper::Default ();
  wifiPhy.SetChannel (wifiChannel.Create ());


  //--------------------------//
  // MESH HELPER CONFIGURATION
  /*
   * Create mesh helper and set stack installer to it
   * Stack installer creates all needed protocols and install them to
   * mesh point device
   */
  std::cout << "-- 1.2 Configurando nó do tipo Mesh\n";
  mesh = MeshHelper::Default ();



  std::cout << "-- 1.2 Configurando o root\n";

  if (!Mac48Address (m_root.c_str ()).IsBroadcast ())
    {
      printf("O Root é: %s\n",m_root.c_str ());
      mesh.SetStackInstaller (m_stack, "Root", Mac48AddressValue (Mac48Address (m_root.c_str ())));
    }
  else
    {
      //If root is not set, we do not use "Root" attribute, because it
      //is specified only for 11s
      mesh.SetStackInstaller (m_stack);
    }


  if (m_chan)
    {
      mesh.SetSpreadInterfaceChannels (MeshHelper::SPREAD_CHANNELS);
    }
  else
    {
      mesh.SetSpreadInterfaceChannels (MeshHelper::ZERO_CHANNEL);
    }
  mesh.SetMacType ("RandomStart", TimeValue (Seconds (m_randomStart)));
  // Set number of interfaces - default is single-interface mesh point
  mesh.SetNumberOfInterfaces (m_nIfaces);
  // Install protocols and return container if MeshPointDevices
  meshDevices = mesh.Install (wifiPhy, nodes);
  // Setup mobility - static grid topology


  //------------------------------------//
  //MOBILITY CONFIGURATION

  std::cout << "-- 1.3 Configurando a topologia em forma de grid\n";

  MobilityHelper mobility;
  mobility.SetPositionAllocator ("ns3::GridPositionAllocator",
                                 "MinX", DoubleValue (0.0),
                                 "MinY", DoubleValue (0.0),
                                 "DeltaX", DoubleValue (m_step),
                                 "DeltaY", DoubleValue (m_step),
                                 "GridWidth", UintegerValue (m_xSize),
                                 "LayoutType", StringValue ("RowFirst"));
  mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
  mobility.Install (nodes);


  if (m_pcap)
    wifiPhy.EnablePcapAll (std::string ("mp-"));
}
///////////////////////////////////////////////////////////////////////////
//                                                                       //
// INTERNET STACK                                                        //
//                                                                       //
///////////////////////////////////////////////////////////////////////////
void
MeshTest::InstallInternetStack ()
{
    NS_LOG_INFO ("Configure Internet Stack.");
    std::cout << "\n2. Configurando a pilha Internet...\n";

  InternetStackHelper internetStack;
  internetStack.Install (nodes);
  Ipv4AddressHelper address;
  address.SetBase ("10.1.1.0", "255.255.255.0");
  interfaces = address.Assign (meshDevices);
}
///////////////////////////////////////////////////////////////////////////
//                                                                       //
// INSTALL APPLICATION                                                   //
//                                                                       //
///////////////////////////////////////////////////////////////////////////
void
MeshTest::InstallApplication ()
{
   NS_LOG_INFO ("InstallApplication.");
   std::cout << "\n3. Configurando a aplicação...\n";

   //SERVER
  std::cout << "--3.1 Configurando aplicação no root (servidor). Nó nº 0 da grade.\n";
  UdpEchoServerHelper echoServer (9);
  ApplicationContainer serverApps = echoServer.Install (nodes.Get (0));
  serverApps.Start (Seconds (0.0));
  serverApps.Stop (Seconds (m_totalTime));

  //CLIENT
  UdpEchoClientHelper echoClient (interfaces.GetAddress (0), 9);
  echoClient.SetAttribute ("MaxPackets", UintegerValue ((uint32_t)(m_totalTime*(1/m_packetInterval))));
  echoClient.SetAttribute ("Interval", TimeValue (Seconds (m_packetInterval)));
  echoClient.SetAttribute ("PacketSize", UintegerValue (m_packetSize));

  std::cout << "--3.1 Configurando aplicação no cliente. Nó nº "<< m_cliente << " da grade\n";
  ApplicationContainer clientApps = echoClient.Install (nodes.Get (m_cliente-1));
  clientApps.Start (Seconds (0.0));
  clientApps.Stop (Seconds (m_totalTime));
}
///////////////////////////////////////////////////////////////////////////
//                                                                       //
// RUN                                                                   //
//                                                                       //
///////////////////////////////////////////////////////////////////////////
int
MeshTest::Run ()
{
  CreateNodes ();
  InstallInternetStack ();
  InstallApplication ();

  NS_LOG_INFO ("------------------ Run Simulation ------------------\n");
  std::cout << "\n4. Rodando Simulação\n";

  FlowMonitorHelper flowmon;
  Ptr<FlowMonitor> monitor = flowmon.InstallAll ();

  Simulator::Schedule (Seconds (m_totalTime), &MeshTest::Report, this);
  Simulator::Stop (Seconds (m_totalTime));
  Simulator::Run ();

  std::ofstream tracesFile("mesh-final.out",std::ios::app);

  monitor->CheckForLostPackets ();
  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier> (flowmon.GetClassifier ());
  std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats ();
  for (std::map<FlowId, FlowMonitor::FlowStats>::const_iterator i = stats.begin (); i != stats.end (); ++i)
  {
      Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow (i->first);
      if (i->second.rxBytes > 0){
          std::cout << "  Flow " << i->first << " (" << t.sourceAddress << " -> " << t.destinationAddress << ")\n";
          //std::cout << "  TxBytes:                     " << i->second.txBytes << "\n";
          //std::cout << "  RxBytes:                     " << i->second.rxBytes << "\n";
          std::cout << "  TxPackets:                   " << i->second.txPackets << "\n";
          std::cout << "  RxPackets:                   " << i->second.rxPackets << "\n";
          std::cout << "  Throughput:                  " << i->second.rxBytes * 8.0 / 10.0 / 1024 / 1024  << " Mbps\n";
          std::cout << "  LostPackets:				   " << i->second.lostPackets << "\n";
          std::cout << "  DeliveyRate:                 " << (i->second.rxPackets * 100.0)/ (i->second.txPackets)  << " %\n";
          //std::cout << "  DelaySum:                    " << i->second.delaySum.GetSeconds()<< " s\n";
          std::cout << "  DelayMean:                   " << (i->second.delaySum.GetSeconds()) / (i->second.rxPackets) << " s\n";
          //std::cout << "  JitterSum:                   " << i->second.jitterSum.GetSeconds()<< " s\n";
          std::cout << "  JitterMean:                  " << (i->second.jitterSum.GetSeconds()) / (i->second.rxPackets -1)<< " s\n";
          std::cout << "  TimesForwarded:              " << i->second.timesForwarded << "\n";
          std::cout << "  TimeFirstTxPacket:           " << i->second.timeFirstTxPacket.GetSeconds() << " s\n";
          std::cout << "  TimeLastTxPacket:            " << i->second.timeLastTxPacket.GetSeconds() << " s\n";
          std::cout << "  TimeFirstRxPacket:           " << i->second.timeFirstRxPacket.GetSeconds() << " s\n";
          //std::cout << "  TimeLastRxPacket:            " << i->second.timeLastRxPacket.GetSeconds() << " s\n";
          //std::cout << "  MeanTransmittedPacketSize:   " << (i->second.txBytes) / (i->second.txPackets) << " byte\n";
          //std::cout << "  MeanTransmittedBitrate:      " << ((i->second.txBytes) * 8.0) / ((i->second.timeLastTxPacket.GetSeconds())-(i->second.timeFirstTxPacket.GetSeconds())) << " bit/s\n";
          //std::cout << "  MeanHopCount:                " << (i->second.timesForwarded) / (i->second.rxPackets) + 1 << "\n";
          //std::cout << "  PacketLossRatio:             " << (i->second.lostPackets) / ((i->second.rxPackets)+(i->second.lostPackets)) << "\n";
          //std::cout << "  MeanReceivedPacketSize:      " << (i->second.rxBytes) / (i->second.rxPackets) << " byte\n";
          //std::cout << "  MeanReceivedBitrate:         " << ((i->second.rxBytes)* 8.0) / ((i->second.timeLastRxPacket.GetSeconds())-(i->second.timeFirstRxPacket.GetSeconds())) << " bit/s \n";
      }
  }

  Simulator::Destroy ();
  return 0;
}
///////////////////////////////////////////////////////////////////////////
//                                                                       //
// REPORT                                                                //
//                                                                       //
///////////////////////////////////////////////////////////////////////////
void
MeshTest::Report ()
{
  std::cout << "\n5. Relatórios da simulação:\n";

  unsigned n (0);
  for (NetDeviceContainer::Iterator i = meshDevices.Begin (); i != meshDevices.End (); ++i, ++n)
    {
      std::ostringstream os;
      os << "mp-report-" << n << ".xml";
      std::cerr << "Printing mesh point device #" << n << " diagnostics to " << os.str () << "\n";
      std::ofstream of;
      of.open (os.str ().c_str ());
      if (!of.is_open ())
        {
          std::cerr << "Error: Can't open file " << os.str () << "\n";
          return;
        }
      mesh.Report (*i, of);
      of.close ();
    }
}
///////////////////////////////////////////////////////////////////////////
//                                                                       //
// MAIN                                        wa                          //
//                                                                       //
///////////////////////////////////////////////////////////////////////////
int
main (int argc, char *argv[])
{
  printf("\n********************************\nMesh 802.11s\n********************************\n");
  MeshTest t;
  t.Configure (argc, argv);
  return t.Run ();
}
