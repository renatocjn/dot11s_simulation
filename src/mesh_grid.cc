/* -*- mode:c++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */

//	Arquvo inicialmente copiado dos exemplos do modulo de mesh do ns3
//	Tem como objetivo simular topologias de mesh

/*
* Copyright (c) 2008,2009 IITP RAS
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
* Author: Kirill Andreev <andreev@iitp.ru>
*
*
* By default this script creates m_xSize * m_ySize square grid topology with
* IEEE802.11s stack installed at each node with peering management
* and HWMP protocol.
* The side of the square cell is defined by m_step parameter.
* When topology is created, UDP ping is installed to opposite corners
* by diagonals. packet size of the UDP ping and interval between two
* successive packets is configurable.
*
*  m_xSize * step
*  |<--------->|
*   step
*  |<--->|
*  * --- * --- * <---Ping sink  _
*  | \   |   / |                ^
*  |   \ | /   |                |
*  * --- * --- * m_ySize * step |
*  |   / | \   |                |
*  | /   |   \ |                |
*  * --- * --- *                _
*  ^ Ping source
*
*  See also MeshTest::Configure to read more about configurable
*  parameters.
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

#include <ctime>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <fstream>

#define EOL '\n' //EOL = End Of Line

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
	unsigned int m_serverId;
	unsigned int m_clientId;
	double m_waitTime;
	Ptr<FlowMonitor> m_flowMonitor;

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
m_step (100), //43.125
m_randomStart (0.3),
m_totalTime (100.0),
m_packetInterval (0.1),
m_packetSize (1024),
m_nIfaces (2),
m_chan (true),
m_pcap (false),
m_stack ("ns3::Dot11sStack"),
m_root ("ff:ff:ff:ff:ff:ff"),
m_serverId (0),
m_clientId(0),
m_waitTime(5.0)
{
}
void
MeshTest::Configure (int argc, char *argv[])
{
	srand(time(NULL));
	CommandLine cmd;
	cmd.AddValue ("x-size", "Number of nodes in a row grid. [3]", m_xSize);
	cmd.AddValue ("y-size", "Number of rows in a grid. [3]", m_ySize);
	cmd.AddValue ("step",   "Size of edge in our grid, meters. [100 m]", m_step);
	/*
	* As soon as starting node means that it sends a beacon,
	* simultaneous start is not good.
	*/
	cmd.AddValue ("start",  "Maximum random start delay, seconds. [0.3 s]", m_randomStart);
	cmd.AddValue ("time",  "Simulation time, seconds [100 s]", m_totalTime);
	cmd.AddValue ("packet-interval",  "Interval between packets in UDP ping, seconds [0.001 s]", m_packetInterval);
	cmd.AddValue ("packet-size",  "Size of packets in UDP ping", m_packetSize);
	cmd.AddValue ("interfaces", "Number of radio interfaces used by each mesh point. [2]", m_nIfaces);
	cmd.AddValue ("channels",   "Use different frequency channels for different interfaces. [0]", m_chan);
	cmd.AddValue ("pcap",   "Enable PCAP traces on interfaces. [0]", m_pcap);
	cmd.AddValue ("stack",  "Type of protocol stack. ns3::Dot11sStack by default", m_stack);
	cmd.AddValue ("root", "Mac address of root mesh point in HWMP", m_root);
	cmd.AddValue ("client", "Id of the client of the UDP ping [default is the node with the largest Id]", m_clientId);
	cmd.AddValue ("server", "Id of the server of the UDP ping [0]", m_serverId);
	cmd.AddValue ("wait-time", "Time waited before starting aplications [5 s]", m_waitTime);
	cmd.Parse (argc, argv);

	SeedManager::SetSeed(rand());

	NS_LOG_DEBUG ("Grid:" << m_xSize << "*" << m_ySize);
	NS_LOG_DEBUG ("Simulation time: " << m_totalTime << " s");
}
void
MeshTest::CreateNodes ()
{
	/*
	* Create m_ySize*m_xSize stations to form a grid topology
	*/
	nodes.Create (m_ySize*m_xSize);

	// Configure YansWifiChannel
	YansWifiPhyHelper wifiPhy = YansWifiPhyHelper::Default ();
	YansWifiChannelHelper wifiChannel = YansWifiChannelHelper::Default ();
	wifiPhy.SetChannel (wifiChannel.Create ());
	/*
	* Create mesh helper and set stack installer to it
	* Stack installer creates all needed protocols and install them to
	* mesh point device
	*/
	mesh = MeshHelper::Default ();
	if (!Mac48Address (m_root.c_str ()).IsBroadcast ())
	{
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
	MobilityHelper mobility;
	mobility.SetPositionAllocator ("ns3::GridPositionAllocator",
								"MinX", DoubleValue (0.0), "MinY", DoubleValue (0.0),
								"DeltaX", DoubleValue (m_step), "DeltaY", DoubleValue (m_step),
								"GridWidth", UintegerValue (m_xSize),
								"LayoutType", StringValue ("RowFirst"));
	mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
	mobility.Install (nodes);
	if (m_pcap)
		wifiPhy.EnablePcapAll (std::string ("mp-"));
}
void
MeshTest::InstallInternetStack ()
{
	InternetStackHelper internetStack;
	internetStack.Install (nodes);
	Ipv4AddressHelper address;
	address.SetBase ("10.1.1.0", "255.255.255.0");
	interfaces = address.Assign (meshDevices);
}
void
MeshTest::InstallApplication ()
{
	UdpEchoServerHelper echoServer (9);
	ApplicationContainer serverApps = echoServer.Install (nodes.Get (m_serverId));
	serverApps.Start (Seconds (m_waitTime));
	serverApps.Stop (Seconds (m_totalTime));
	UdpEchoClientHelper echoClient (interfaces.GetAddress (m_serverId), 9);
	echoClient.SetAttribute ("MaxPackets", UintegerValue ((uint32_t)((m_totalTime-m_waitTime)*(1/m_packetInterval))));
	echoClient.SetAttribute ("Interval", TimeValue (Seconds (m_packetInterval)));
	echoClient.SetAttribute ("PacketSize", UintegerValue (m_packetSize));
	ApplicationContainer clientApps = echoClient.Install (nodes.Get (m_clientId));
	clientApps.Start (Seconds (m_waitTime));
	clientApps.Stop (Seconds (m_totalTime));
}
int
MeshTest::Run ()
{
	m_clientId = m_xSize * m_ySize - 1; //valor default
	CreateNodes ();
	InstallInternetStack ();
	InstallApplication ();
	// Flow monitor initialization
	FlowMonitorHelper fmh;
	fmh.InstallAll();
	m_flowMonitor = fmh.GetMonitor();

	Simulator::Schedule (Seconds (m_totalTime), &MeshTest::Report, this);
	Simulator::Stop (Seconds (m_totalTime));
	Simulator::Run ();
	Simulator::Destroy ();
	m_flowMonitor->CheckForLostPackets();
	m_flowMonitor->SerializeToXmlFile("FlowMonitorResults.xml", true, true);
	return 0;
}
void
MeshTest::Report ()
{
	unsigned n (0);
	for (NetDeviceContainer::Iterator i = meshDevices.Begin (); i != meshDevices.End (); ++i, ++n)
	{
		std::ostringstream os;
		os << "mp-report-" << n << ".xml";
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
int
main (int argc, char *argv[])
{
	MeshTest t;
	t.Configure (argc, argv);
	return t.Run ();
}