/* -*- mode:c++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */

//	Arquvo inicialmente copiado dos exemplos do modulo de mesh do ns3
//	Tem como objetivo simular topologias de mesh

#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "ns3/applications-module.h"
#include "ns3/wifi-module.h"
#include "ns3/mesh-module.h"
#include "ns3/mobility-module.h"
#include "ns3/mesh-helper.h"
#include "ns3/random-variable.h"
#include "ns3/flow-monitor-module.h"

#include <ctime>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <fstream>
#include <set>
#include <cmath>
#include <list>
#include <unistd.h>
#include <cstdio>

#define EOL std::endl //EOL = End Of Line
#define MAX_RETRIES 10

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("TestMeshScript");
class MeshTest
{
public:
	MeshTest ();

	void Configure (int argc, char ** argv);

	int Run ();

private:
	unsigned int m_radius;
	unsigned int m_numberNodes;
	unsigned int m_nFlows;
	double    m_randomStart;
	double    m_totalTime;
	double    m_packetInterval;
	uint16_t  m_packetSize;
	uint32_t  m_nIfaces;
	bool      m_chan;
	bool      m_pcap;
	std::string m_stack;
	std::string m_root;
	std::string m_minimumNumberOfNeighbors;
	unsigned int m_serverId;
	double m_waitTime;

	Ptr<FlowMonitor> m_flowMonitor;
	NodeContainer nodes;
	NetDeviceContainer meshDevices;
	Ipv4InterfaceContainer interfaces;
	MeshHelper mesh;
	std::list<Vector> m_positions;

private:
	void CreateNodes ();
	void InstallInternetStack ();
	void InstallApplication ();
	void Report ();
	bool checkRunForConnections(); // calls external script to check latest run for the minimum number of connections
	void setupRandomMobility();
	void generateValidPositions();
	void loadPositions();
};

MeshTest::MeshTest () :
	m_radius (500),
	m_numberNodes (50),
	m_nFlows (1),
	m_randomStart (0.1),
	m_totalTime (100.0),
	m_packetInterval (0.1),
	m_packetSize (1024),
	m_nIfaces (2),
	m_chan (true),
	m_pcap (false),
	m_stack ("ns3::Dot11sStack"),
	m_root ("00:00:00:00:00:01"),
	m_minimumNumberOfNeighbors ("3"),
	m_serverId (0),
	m_waitTime(5.0) {}

int main (int argc, char *argv[]) {
	MeshTest t;
	t.Configure (argc, argv);
	return t.Run ();
}

void MeshTest::Configure (int argc, char *argv[]) {
	srand(time(NULL));
	CommandLine cmd;
	cmd.AddValue ("radius", "Radius of the disk that the mesh points are located. [150 m]", m_radius);
	cmd.AddValue ("number-of-nodes",  "Number of nodes in the simulation. [50]", m_numberNodes);
	cmd.AddValue ("flows", "Number of flows in the simulation. [1]", m_nFlows);
	cmd.AddValue ("neighbors",  "Minimum number of neighbors per node. [3]", m_minimumNumberOfNeighbors);

	cmd.AddValue ("start",  "Maximum random start delay, seconds. [0.1 s]", m_randomStart);
	cmd.AddValue ("time",  "Simulation time, seconds [100 s]", m_totalTime);

	cmd.AddValue ("packet-interval",  "Interval between packets in UDP ping, seconds [0.001 s]", m_packetInterval);
	cmd.AddValue ("packet-size",  "Size of packets in UDP ping", m_packetSize);
	cmd.AddValue ("interfaces", "Number of radio interfaces used by each mesh point. [2]", m_nIfaces);
	cmd.AddValue ("channels",   "Use different frequency channels for different interfaces. [1]", m_chan);
	cmd.AddValue ("wait-time", "Time waited before starting aplications [5 s]", m_waitTime);

	cmd.AddValue ("pcap",   "Enable PCAP traces on interfaces. [0]", m_pcap);

	cmd.Parse (argc, argv);

	NS_LOG_DEBUG ("Random Disk area with " << m_numberNodes << " nodes");
	NS_LOG_DEBUG ("Simulation time: " << m_totalTime << " s");

	int seed = rand();
// 	std::cout << "[Mesh Random Disc] seed: " << seed << EOL;
	SeedManager::SetSeed(seed);
}

int MeshTest::Run () {
	generateValidPositions();

	CreateNodes ();
	loadPositions();
	InstallInternetStack ();
	InstallApplication ();

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

void MeshTest::CreateNodes () {
	nodes = NodeContainer();
	nodes.Create (m_numberNodes);

	YansWifiPhyHelper wifiPhy = YansWifiPhyHelper::Default ();
	YansWifiChannelHelper wifiChannel = YansWifiChannelHelper::Default ();
	wifiPhy.SetChannel (wifiChannel.Create ());

	mesh = MeshHelper::Default ();
	mesh.SetStackInstaller (m_stack, "Root", Mac48AddressValue (Mac48Address (m_root.c_str ())));

	if (m_chan)
	{
		mesh.SetSpreadInterfaceChannels (MeshHelper::SPREAD_CHANNELS);
	}
	else
	{
		mesh.SetSpreadInterfaceChannels (MeshHelper::ZERO_CHANNEL);
	}

	mesh.SetMacType ("RandomStart", TimeValue (Seconds (m_randomStart)));
	mesh.SetNumberOfInterfaces (m_nIfaces);
	meshDevices = mesh.Install (wifiPhy, nodes);

	if (m_pcap)
		wifiPhy.EnablePcapAll (std::string ("mp-"));
}

void MeshTest::InstallInternetStack () {
	InternetStackHelper internetStack;
	internetStack.Install (nodes);
	Ipv4AddressHelper address;
	address.SetBase ("10.1.1.0", "255.255.255.0");
	interfaces = address.Assign (meshDevices);
}

void MeshTest::InstallApplication () {
	double totalTransmittingTime = m_totalTime - 1.0;

	UdpEchoServerHelper echoServer (9);
	ApplicationContainer serverApps = echoServer.Install (nodes.Get (m_serverId));
	serverApps.Start (Seconds (m_waitTime));
	serverApps.Stop (Seconds (totalTransmittingTime));

	UdpEchoClientHelper echoClient (interfaces.GetAddress (m_serverId), 9);
	echoClient.SetAttribute ("MaxPackets", UintegerValue ((uint32_t)((totalTransmittingTime-m_waitTime)*(1/m_packetInterval))));
	echoClient.SetAttribute ("Interval", TimeValue (Seconds (m_packetInterval)));
	echoClient.SetAttribute ("PacketSize", UintegerValue (m_packetSize));

	std::set<int> clientIds;
	do {
		int n = (rand() + 1) % m_numberNodes;
		clientIds.insert(n);
	} while (clientIds.size() < m_nFlows);

	NodeContainer clients;
	for (std::set<int>::iterator it = clientIds.begin(); it != clientIds.end(); it++) {
		clients.Add(nodes.Get (*it));
	}

	ApplicationContainer clientApps = echoClient.Install (clients);
	clientApps.Start (Seconds (m_waitTime));
	clientApps.Stop (Seconds (totalTransmittingTime));
}

void MeshTest::setupRandomMobility() {
	MobilityHelper mobility;

	Ptr<UniformRandomVariable> rho = CreateObject<UniformRandomVariable>();
	rho->SetAttribute("Min", DoubleValue(0.0));
	rho->SetAttribute("Max", DoubleValue(m_radius));

	Ptr<RandomDiscPositionAllocator> positionAllocator = CreateObject<RandomDiscPositionAllocator>();
	positionAllocator->SetX(m_radius);
	positionAllocator->SetY(m_radius);
	positionAllocator->SetRho(rho);

	mobility.SetPositionAllocator(positionAllocator);

	mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
	mobility.Install (nodes);
}

void MeshTest::generateValidPositions() {
	std::cout << "[Mesh Random Disc] generating positions..."<< EOL;
	for( int i=0; i<MAX_RETRIES && m_positions.empty(); i++ ) {
		CreateNodes ();
		setupRandomMobility();
		InstallInternetStack ();

		Simulator::Schedule (Seconds (m_waitTime), &MeshTest::Report, this);
		Simulator::Stop (Seconds (m_waitTime));
		Simulator::Run ();

		bool itWasValid = checkRunForConnections();
		std::cout << "[Mesh Random Disc] itWasValid: " << itWasValid << EOL;
		if ( itWasValid ) {
			for (uint32_t i=0; i<nodes.GetN(); i++) {
				ns3::Vector p = nodes.Get(i)->GetObject<MobilityModel>()->GetPosition();
				m_positions.push_back(p);
			}
		}
		Simulator::Destroy ();
	}

	FILE* fp = std::fopen("positions.txt", "w");
	for (uint32_t i=0; i<nodes.GetN(); i++) {
		ns3::Vector p = nodes.Get(i)->GetObject<MobilityModel>()->GetPosition();
		fprintf(fp, "%d|%f|%f\n", i, p.x, p.y);
	}

	if(m_positions.empty()) {
		for( unsigned i=0; i<m_numberNodes; i++) {
			std::ostringstream os;
			os << "mp-report-"<< i << ".xml";
			std::remove(os.str().c_str());
		}
		std::cout << "Maximum of retries for the topology were run! Aborting..." << EOL;
 		std::exit(0);
	}
}

bool MeshTest::checkRunForConnections() {
	/// Not the nicest way but couldn't find a better one ~RenatoCJN

// 	char path[256];
// 	std::cout << getcwd(path, 255) << EOL;
// 	std::ostringstream os;
//  	os << "../../../check.py"

	/// The program must exit with 1 for a valid run and 0 for a invalid run
	if (system( "../../../check.py" ) == 0)
		return true;
	else
		return false;
}

void MeshTest::loadPositions() {
	MobilityHelper mobility;

	Ptr<ListPositionAllocator> positionAllocator = CreateObject<ListPositionAllocator>();
	for (std::list<Vector>::iterator p=m_positions.begin(); p != m_positions.end(); ++p) {
		positionAllocator->Add(*p);
	}

	mobility.SetPositionAllocator(positionAllocator);

	mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
	mobility.Install (nodes);
}

void MeshTest::Report () {
	unsigned n (0);
	for (NetDeviceContainer::Iterator i = meshDevices.Begin (); i != meshDevices.End (); ++i, ++n)
	{
		std::ostringstream os;
		os << "mp-report-" << n << ".xml";
		std::ofstream of;
		of.open (os.str ().c_str ());
		if (!of.is_open ())
		{
			std::cerr << "Error: Can't open file " << os.str () << EOL;
			return;
		}
		mesh.Report (*i, of);
		of.close ();
	}
}
